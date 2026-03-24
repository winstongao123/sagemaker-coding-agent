def broken_function()
    """This function has a syntax error - missing colon after def"""
    print("Hello, World!")
    return 42

def working_function():
    """This function is correct"""
    print("This works!")
    return True

if __name__ == "__main__":
    working_function()
