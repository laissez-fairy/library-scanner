def ldist(s1: str, s2: str) -> int:
    """Returns the Levenshtein distance between two strings.

    Gives the notion of similarity considering typos.
    Calculated in O(m + n) time with dynamic programming.

    Args: s1 (str): usually a search query
          s2 (str): usually a potential result

    Returns:
        int: Levenshtein distance between s1 and s2.
        """
    m = len(s1)
    n = len(s2)

    dp = [[0 for i in range(n+1)] for j in range(m+1)]

    for i in range(m+1):
        dp[i][0] = i
    for j in range(n+1):
        dp[0][j] = j

    for i in range(1, m+1):
        for j in range(1, n+1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i][j-1], dp[i-1][j], dp[i-1][j-1])

    return dp[m][n]

def fuzzymatch(s1, s2):
    if ldist(s1, s2) < len(s1 + s2) / 2:
        return True
    else:
        return False