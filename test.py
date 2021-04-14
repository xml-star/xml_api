def totalNQueens(n):
    res = 0  # res => 用于存储方案数

    lie = [False] * n  # lie => 用于判断当前列是否有皇后
    dui1 = [False] * (2 * n - 1)  # dui1 左下->右上的对角线
    dui2 = [False] * (2 * n - 1)  # dui2 左上->右下的对角线

    # i => 当前该在哪一行放置皇后
    def dfs(i):
        nonlocal res

        if i == n:
            res += 1
            return

        for j in range(0, n):
            if not lie[j] and not dui1[i + j] and not dui2[i - j + n - 1]:
                lie[j] = True
                dui1[i + j] = True
                dui2[i - j + n - 1] = True
                dfs(i + 1)
                lie[j] = False
                dui1[i + j] = False
                dui2[i - j + n - 1] = False

    dfs(0)
    return res

totalNQueens(4)