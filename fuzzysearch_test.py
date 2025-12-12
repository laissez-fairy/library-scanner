import pytest
from fuzzysearch import *

def test_fuzzysearch():
    assert ldist('car', 'daramel') == 5  # add assertion here
def test_fuzzysearch_2():
    assert ldist('15', '151') == 1
def test_fuzzysearch_3():
    assert ldist('15', '') == 2
def test_fuzzysearch_4 ():
    assert ldist('15', '15') == 0


if __name__ == '__main__':
    pytest.main()
