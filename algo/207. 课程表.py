# 207. 课程表
# 你这个学期必须选修 numCourses 门课程，记为 0 到 numCourses - 1 。
# 在选修某些课程之前需要一些先修课程。 先修课程按数组 prerequisites 给出
# 其中 prerequisites[i] = [ai, bi] ，表示如果要学习课程 ai 则 必须 先学习课程  bi 。
# 例如，先修课程对 [0, 1] 表示：想要学习课程 0 ，你需要先完成课程 1 。
# 请你判断是否可能完成所有课程的学习？如果可以，返回 true ；否则，返回 false 。
#
# 示例 1：
# 输入：numCourses = 2, prerequisites = [[1,0]]
# 输出：true
# 解释：总共有 2 门课程。学习课程 1 之前，你需要完成课程 0 。这是可能的。

def fun(numCourses, prerequisites):
    numC = [0] * numCourses
    preC = [[] for _ in range(numCourses)]

    for cur, pre in prerequisites:
        numC[cur] += 1
        preC[pre].append(cur)

    stack = [i for i in range(numCourses) if numC[i] == 0]

    cnt = 0
    while stack:
        c = stack.pop()
        cnt += 1
        for cour in preC[c]:
            numC[cour] -= 1
            if numC[cour] == 0:
                stack.append(cour)

    return cnt == numCourses

if __name__ == '__main__':
    numCourses = 2
    prerequisites = [[1, 0]]
    print(fun(numCourses, prerequisites))