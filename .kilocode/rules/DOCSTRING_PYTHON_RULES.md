# Guide to Creating and Generating Docstrings

This guide provides comprehensive standards for writing effective docstrings and documentation comments in Python(*.py) files.

## Python Docstring Guidelines

The official standard for Python docstrings is defined in [PEP 257](https://www.python.org/dev/peps/pep-0257/).

*   **Placement**: A docstring must be the first statement in a module, function, class, or method.
*   **Format**: Always use triple double quotes (`"""Docstring goes here"""`).

### One-line Docstrings
Ideal for simple functions. It should be a concise summary ending with a period.

```python
def square(num):
    """Return the square of a number."""
    return num * num
```

### Multi-line Docstrings
These start with a one-line summary, followed by a blank line, and then a more detailed description. While PEP 257 provides the base, structured formats like Google and NumPy are widely used for better readability and tool integration.

**Google Style:**
Readable and clean, recommended by the Google Python Style Guide.

```python
def add(a, b):
    """Adds two numbers.

    Args:
        a (int): The first number.
        b (int): The second number.

    Returns:
        int: The sum of a and b.
    """
    return a + b
```
