# 54. 螺旋矩阵
# 给你一个 m 行 n 列的矩阵 matrix ，请按照 顺时针螺旋顺序 ，返回矩阵中的所有元素。
#
# 示例 1：
# 输入：matrix = [[1,2,3],[4,5,6],[7,8,9]]
# 输出：[1,2,3,6,9,8,7,4,5]

def fun(matrix):
    m, n = len(matrix), len(matrix[0])
    i = j = 0
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    di = 0
    res = []

    for _ in range(m * n):
        res.append(matrix[i][j])
        matrix[i][j] = None

        next_i = i + directions[di][0]
        next_j = j + directions[di][1]

        if next_i >= m or next_i < 0 or next_j >= n or next_j < 0 or matrix[next_i][next_j] is None:
            di = (di + 1) % 4

        i += directions[di][0]
        j += directions[di][1]

    return res

if __name__ == '__main__':
    matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    print(fun(matrix))