from prefect import task, Flow, Parameter


@task
def add(a: int, b: int) -> int:
    """Task to add two numbers together

    .. note::
          Admonitions work too!

    Parameters
    ----------
    :param a:
          The first int
    :param b:
          The second int

    Returns
    -------
    :return: The sum of two input numbers
    :rtype: int
    """
    return a + b


@task
def multi(prev_result: int) -> int:
    """Task to multiply the previous result by 5

    :param: Previous calculations result

    :return: Returns the input number multiplied by 5
    :rtype: int
    """
    return prev_result * 5


with Flow(name="aham-flow") as flow:
    a = Parameter(name="a", default=1)
    b = Parameter(name="b", default=1)
    r = add(a, b)
    multi(r)
