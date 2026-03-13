# Contributing Guide

Thank you for contributing to this project. Please follow the workflow below when making changes.

## 1. Clone the Repository

First clone the repository to your local machine.

```
git clone https://github.com/<username>/<repository>.git
cd <repository>
```

---

## 2. Create a New Branch

Do **not modify the `main` branch directly**.

Create a new branch for your changes:

```
git checkout -b feature/your-feature-name
```

Example:

```
git checkout -b feature/add-image-export
```

---

## 3. Make Your Changes

Modify the necessary files and test your changes locally.

---

## 4. Commit Your Changes

Stage your changes:

```
git add .
```

Create a commit:

```
git commit -m "Add short description of the change"
```

Example:

```
git commit -m "Add new image export function"
```

---

## 5. Push the Branch to GitHub

Push your branch to the remote repository:

```
git push origin feature/your-feature-name
```

---

## 6. Create a Pull Request

1. Go to the repository on GitHub.
2. Click **"Compare & Pull Request"**.
3. Provide a short description of your changes.
4. Submit the pull request.

The project maintainer will review the changes and either merge the pull request or request modifications.

---

## Summary Workflow

```
git clone <repo>
git checkout -b feature/my-feature
# make changes
git add .
git commit -m "Description of change"
git push origin feature/my-feature
```

Then open a **Pull Request** on GitHub.
