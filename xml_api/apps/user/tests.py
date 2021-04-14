# class Solution:
#     def permute(self, nums):
#         n = len(nums)
#
#         st = [False]*n
#         res = []
#
#         # u：代表当前该填位置的下标
#         # cur：存储当前排列
#         def dfs(u,cur):
#             if u == n:
#                 res.append(list(cur))
#                 return
#             for i in range(0,n):
#                 if st[i]:continue
#                 st[i]=True
#                 dfs(u+1,cur+[nums[i]])
#                 st[i]=False
#         dfs(0,[])
#         return res
# a = Solution()
# a.permute([1,2])