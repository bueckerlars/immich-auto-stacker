# Python Project Template

This repository serves as a template for initializing Python projects on GitHub. It provides a basic structure and configuration files to help you get started quickly with your Python projects.

## Getting Started

To use this template for your Python project, follow these steps:

1. Click on the "Use this template" button at the top of this repository.
2. Provide a name for your new repository.
3. Optionally, provide a description for your new repository.
4. Choose the visibility (internal or private) for your new repository.
5. Click on the "Create repository from template" button.

After you have initialized your repository from this template and have cloned it to your local machine, adapt the following:
- Rename the package `python-template` in the source code directory `src` to your desired package name.
- Adapt the `pyproject.toml` file:
    - Within the section `[project]`, adapt the keys `description` and `name`. Make further changes to keys as you see fit.
    - Within the section `[project.urls]`, adapt both keys `"Bug Tracker"`  and `"Homepage"`.
- Adapt the `Dockerfile`:
    - Update the `CMD` instruction to match your package name and entry point (e.g., change `python-template.main` to `your-package-name.main`).
- Change the content of the `README.md` file, giving users of your package brief information about the purpose of your package, as well as how they can install and use your package.

Then, install your project and start coding:
```bash
uv sync --all-extras
pre-commit install
```

## Project Structure
The template follows a specific structure to organize your project files:

- `src/`: This directory is where the main source code of the project resides.
- `src/my_project`: This directory contains the source code regarding your Python **package** (here: called `my_project`).
- `tests/`: This directory contains the unit tests for the project.
- `README.md`: This file provides an overview of the project and its purpose.
- `pyproject.toml`: This file is used for managing project dependencies and build configurations.
- `.pre-commit-config.yaml`: This file contains the configuration for pre-commit hooks, which are used for code quality checks and formatting.
- `.gitignore`: This file specifies which files and directories should be ignored by Git.



## Application Context, Inversion of Control, and Dependency Injection

Your new project should use an **Application Context** as a deliberate architectural pattern to wire and assemble the application.

The goal of the application context is simple:

> **Assemble the application once, at startup, and never let domain or service code care about how dependencies are created.**

This pattern exists mainly to keep database sessions, repositories, services, and infrastructure concerns properly separated.


### What the Application Context is

The application context is:

* a **composition root**
* a **dependency wiring container**
* a **factory for fully-initialized services**

It is the single place where:

* settings are loaded
* infrastructure clients are created (Postgres, Redis, etc.)
* repositories are constructed
* services are constructed with all dependencies already provided

In short:
**all wiring happens here, and only here.**

Once the context is created, the rest of the application *only* consumes what it provides. It must never care about *how* things are created.


### What the Application Context is *not*

The application context is **not**:

* a singleton registry
* a global object you pull things from
* a place to *look up* dependencies from inside services
* a service locator

Services must never call into the application context to fetch dependencies.


### What is a Composition Root?

The application context acts as the **composition root** of the application.

A composition root is the **one place in your application where the object graph is built**.

This means:
- all services
- all repositories
- all clients
- all settings
- and all your other objects having dependencies

are created and wired together here - and only here.
After this point, *no new wiring* happens anywhere else. Everything else just uses already-assembled objects. That also means that no object constructs its own dependencies, it only receives them.

The term *wiring* just means initializing objects (like services) and providing them with their dependencies (like repositories, clients, settings, etc.).

**Key Properties:**
- exactly one place
- runs at application startup, called and initialized in your main entry point
- knows *everything*
- nothing else knows how things are wired

**Example**:

```python
class ApplicationContext:
    @property
    def settings(self) -> Settings:
        return Settings()

    @property
    def database_client(self) -> DatabaseClient:
        return DatabaseClient(self.settings.database_url)

    @property
    def user_repository(self) -> UserRepository:
        return UserRepository(self.database_client)

    @property
    def user_service(self) -> UserService:
        return UserService(self.user_repository)
```

Then in your entry point (FastAPI, CLI, Streamlit, etc.):

```python
app_context = ApplicationContext()
user_service = app_context.user_service
# Do some stuff with the user service
return user_service.get_all_users()
```

### Inversion of Control (IoC)

Inversion of Control means that code does **not** control and/or create its own dependencies. Instead, its dependencies are provided from the outside.

Take the user service for example. Instead of the user service acting like this:

> “I need dependency X, I’ll go create it myself”

the service should act like this:

> “I need dependency X, someone else must provide it to me”

The control over *how things are created* is inverted and taken away from the code itself.

**Without IoC (bad)**:

```python
class UserService:
    def __init__(self) -> None:
        self._settings = Settings()
        self._database_client = DatabaseClient(self._settings.database_url)
        self._repository = UserRepository(self._database_client)
```
Here:
- the service controls everything
- it decides concrete implementations
- it is tightly coupled to infrastructure

**With IoC (good)**:

```python
class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository
```
Now:
- the service does **not** control creation of dependencies
- it just declares which dependencies it needs
- something else (the application context) provides its dependencies

Note that IoC is a *principle*, not a tool. Dependency Injection is one way to implement IoC.

### Dependency Injection (DI)

Dependency Injection means:
> Dependencies are provided into an object instead of being created or fetched by the object itself.

In our case, the application context **injects** or **wires** dependencies into services via their constructors.

**Example**:

```python
class ApplicationContext:
    @property
    def settings(self) -> Settings:
        return Settings()

    @property
    def database_client(self) -> DatabaseClient:
        return DatabaseClient(self.settings.database_url)

    @property
    def user_repository(self) -> UserRepository:
        return UserRepository(self.database_client)

    @property
    def user_service(self) -> UserService:
        return UserService(repository=self.user_repository)
```
This is the *cleanest and most explicit* way to declare dependencies.

Thus, the user service above:

* does not know where the repository comes from
* does not know how it was configured
* does not know about settings or environment variables

All of that is handled by the application context.

**Why this is good**:
- dependencies are explicit and visible in the constructor (the user service depends on a user repository)
- easy to test by providing mock or fake dependencies
- no globals
- no hidden dependencies, no hidden magic

**Testing Example**:

```python
def test_user_service() -> None:
    fake_repository = FakeUserRepository()
    service = UserService(repository=fake_repository)
    # Test service methods here
```
No application context. No database clients. No monkey-patching. Just a simple fake repository.

**DI Containers**

Libraries like [dependency-injector](https://python-dependency-injector.ets-labs.org/) or [autowired](https://pypi.org/project/autowired/) just automate the wiring part.
They do not change the fundamental principles of IoC or DI, they just reduce boilerplate.

### Why we do not use a Service Locator

A service locator is a **global object that you ask for dependencies**.

In other words:

> “Hey container, give me dependency X.”

**Example**:

```python
class ApplicationContext:
    @property
    def settings(self) -> Settings:
        return Settings()

    @property
    def datahub_client(self) -> DataHubClient:
        return DataHubClient(self.settings.datahub_url)

class UserService:
    def __init__(self) -> None:
        self._datahub_client = ApplicationContext().datahub_client
```

Here, the service **pulls** what it needs from a globally accessible context.


#### Why this is problematic

##### 1. Hidden dependencies

Looking at the constructor:

```python
class UserService:
    def __init__(self) -> None:
        ...
```

you have no idea what this service actually depends on.
Those dependencies are hidden inside the implementation.

In practice, this makes the code harder to understand, harder to reason about, and easier to misuse. Hidden dependencies are a well-known code smell.


##### 2. Global state and tight coupling

With a service locator:

* everything depends on a global object
* services are implicitly coupled to the application context
* dependencies are not passed explicitly
* dependencies cannot be varied per instance

Even though the dependency exists, it is **not visible at the boundary** of the class. That makes the coupling real, but implicit.


##### 3. Hard to test in isolation

Because dependencies come from a global container, you cannot easily replace them.

To test this service, you would need to:

* monkey-patch the application context
* modify global state
* or bootstrap the entire application

All of these are things we explicitly want to avoid. Services should be easy to construct with mocks or fakes.


##### 4. Violates the inversion of control principle

With a service locator, the service decides *where* its dependencies come from.

Instead of:

> “You give me what I need”

it becomes:

> “I’ll go fetch what I need myself”

That is the opposite of how we use inversion of control in this project.


In short:
**Service locators trade short-term convenience for long-term coupling, hidden dependencies, and poor testability.**
That’s why we don’t use them here.


### Summary

The application context exists to:

* assemble the application once
* keep wiring and construction out of domain code
* enforce explicit dependencies
* avoid global state and service locators

**Services do not pull dependencies.
Dependencies are provided by the application context.**

That convention is intentional and important to keep code clean, testable, and maintainable.

Sure — here’s a tightened-up version that keeps it practical and human, but a bit more deliberate and opinionated.


## Conventions

To keep the codebase consistent and predictable across projects, we follow these conventions:

* Use the **Application Context** pattern as described above.
  All wiring happens in one place; services do not pull dependencies themselves.
* Follow **PEP 8** for general Python style.
* Write **docstrings for all public classes and methods**.
  If something is public, it should be explainable without reading the implementation.
* Use **type hints everywhere**.
  Treat missing types as a bug, not as an optional improvement.
* Use **semantic versioning** for the package.
* Keep the `README.md` **up to date** and make sure it explains how to install, configure, and run the project.
* Use **pre-commit hooks** to enforce formatting and basic quality checks automatically.
* Use **pytest** for all tests.
* Use **pyright** in **strict mode** (or an alternative type checker with equivalent strictness).
  Disabling checks via `# type: ignore[...]` is allowed only when absolutely necessary (for example when dealing with third-party libraries that ship broken or missing type hints).
* Use **ruff** for linting and formatting.
  Do not fight the formatter — fix the code instead.

These rules are not meant to be academic. They exist to keep the codebase readable, testable, and boring to maintain.


## Additional Information
To get yourself more familar with how to create a Python project, some useful additional information can be found here:
- [Python Documentation](https://www.python.org/doc/): a great source of tipps about everything related to Python.
- [PEP 8](https://www.python.org/dev/peps/pep-0008/): style guide for writing Python code.
- [PEP 621](https://peps.python.org/pep-0621/): information how to store project information.
- [py-pkgs](https://py-pkgs.org/): further information revolving around how to create Python packages, testing, CI/CD, building, etc. A really useful source that provide very detailed information. (Note: we slightly modified how they organize a Python project!)
- [pre-commit](https://pre-commit.com/): general information about pre-commit hooks, ensuring code quality, formating and a lot more!
- [Sphinx](https://www.sphinx-doc.org/en/master/): automatically creating API documentation based on your source code.
- [MkDocs](https://www.mkdocs.org/): creating project documentation using Markdown files.
- [Semantic Versioning](https://semver.org/): more detailed information about how to version your Python package.
- [Pytest](https://docs.pytest.org/en/7.4.x/): extensive information about how to write tests for your source code!
- [uv](https://docs.astral.sh/uv/): A modern Python package and dependency manager supporting the latest PEP standards.
