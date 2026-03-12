"""
Generate company-specific DSA questions and push directly to Firebase Firestore.
No intermediate JSON files - questions go straight to the database.
"""
import requests
import copy

API_KEY = "AIzaSyBV-vv02SgZoRzpp0my4niXX-2P-7QngOY"
PROJECT_ID = "syntatic-1"
BASE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"


def python_to_firestore(value):
    if isinstance(value, str):
        return {"stringValue": value}
    elif isinstance(value, bool):
        return {"booleanValue": value}
    elif isinstance(value, int):
        return {"integerValue": str(value)}
    elif isinstance(value, float):
        return {"doubleValue": value}
    elif isinstance(value, list):
        return {"arrayValue": {"values": [python_to_firestore(v) for v in value]}}
    elif isinstance(value, dict):
        return {"mapValue": {"fields": {k: python_to_firestore(v) for k, v in value.items()}}}
    elif value is None:
        return {"nullValue": None}
    else:
        return {"stringValue": str(value)}


def push_company(company, questions):
    url = f"{BASE_URL}/dsa_questions/{company}?key={API_KEY}"

    doc_body = {
        "fields": {
            "company": python_to_firestore(company),
            "questions": python_to_firestore(questions),
            "count": python_to_firestore(len(questions)),
        }
    }

    resp = requests.patch(url, json=doc_body, timeout=30)

    if resp.status_code == 200:
        print(f"  [OK] {company}: {len(questions)} questions pushed to Firebase")
        return True
    else:
        print(f"  [ERROR] {company}: {resp.status_code} - {resp.text[:200]}")
        return False


def q(title, desc, topic, difficulty, examples, constraints):
    return {"title": title, "description": desc, "topic": topic, "difficulty": difficulty,
            "examples": examples, "constraints": constraints}

def ex(inp, out, expl=""):
    return {"input": inp, "output": out, "explanation": expl}

GOOGLE = [
    q("Two Sum", "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.", "Arrays & Hash Maps", "Easy",
      [ex("nums = [2,7,11,15], target = 9", "[0,1]", "nums[0] + nums[1] == 9"), ex("nums = [3,2,4], target = 6", "[1,2]", "nums[1] + nums[2] == 6"), ex("nums = [3,3], target = 6", "[0,1]", "nums[0] + nums[1] == 6")], ["2 <= nums.length <= 10^4", "Only one valid answer exists"]),
    q("Valid Parentheses", "Given a string s containing just '(', ')', '{', '}', '[' and ']', determine if the input string is valid.", "Stacks", "Easy",
      [ex("s = '([])'", "true", "Brackets match correctly"), ex("s = '(]'", "false", "Mismatched brackets"), ex("s = '{[]}'", "true", "Nested brackets valid")], ["1 <= s.length <= 10^4"]),
    q("Merge Two Sorted Lists", "Merge two sorted linked lists and return it as a sorted list.", "Linked Lists", "Easy",
      [ex("l1 = [1,2,4], l2 = [1,3,4]", "[1,1,2,3,4,4]"), ex("l1 = [], l2 = []", "[]"), ex("l1 = [], l2 = [0]", "[0]")], ["0 <= list length <= 50"]),
    q("Best Time to Buy and Sell Stock", "Given array prices, find the maximum profit from buying and selling once.", "Arrays & Greedy", "Easy",
      [ex("prices = [7,1,5,3,6,4]", "5", "Buy at 1, sell at 6"), ex("prices = [7,6,4,3,1]", "0", "No profit possible"), ex("prices = [2,4,1]", "2", "Buy at 2, sell at 4")], ["1 <= prices.length <= 10^5"]),
    q("Maximum Subarray", "Find the contiguous subarray with the largest sum.", "Dynamic Programming", "Easy",
      [ex("nums = [-2,1,-3,4,-1,2,1,-5,4]", "6", "Subarray [4,-1,2,1]"), ex("nums = [1]", "1", "Single element"), ex("nums = [5,4,-1,7,8]", "23", "Entire array")], ["1 <= nums.length <= 10^5"]),
    q("Climbing Stairs", "Each time you can climb 1 or 2 steps. How many distinct ways to reach step n?", "Dynamic Programming", "Easy",
      [ex("n = 2", "2", "1+1 or 2"), ex("n = 3", "3", "1+1+1, 1+2, 2+1"), ex("n = 4", "5", "Five distinct ways")], ["1 <= n <= 45"]),
    q("Symmetric Tree", "Check whether a binary tree is a mirror of itself.", "Trees & BFS", "Easy",
      [ex("root = [1,2,2,3,4,4,3]", "true"), ex("root = [1,2,2,null,3,null,3]", "false"), ex("root = [1]", "true")], ["Node count <= 1000"]),
    q("Maximum Depth of Binary Tree", "Return the maximum depth of a binary tree.", "Trees & DFS", "Easy",
      [ex("root = [3,9,20,null,null,15,7]", "3"), ex("root = [1,null,2]", "2"), ex("root = []", "0")], ["Node count <= 10^4"]),
    q("Invert Binary Tree", "Invert a binary tree (swap all left and right children).", "Trees", "Easy",
      [ex("root = [4,2,7,1,3,6,9]", "[4,7,2,9,6,3,1]"), ex("root = [2,1,3]", "[2,3,1]"), ex("root = []", "[]")], ["Node count <= 100"]),
    q("Single Number", "Every element appears twice except one. Find it in O(n) time, O(1) space.", "Bit Manipulation", "Easy",
      [ex("nums = [4,1,2,1,2]", "4"), ex("nums = [2,2,1]", "1"), ex("nums = [1]", "1")], ["1 <= nums.length <= 3*10^4"]),
    q("Linked List Cycle", "Determine if a linked list has a cycle.", "Linked Lists & Two Pointers", "Easy",
      [ex("head = [3,2,0,-4], pos = 1", "true", "Tail connects to index 1"), ex("head = [1,2], pos = 0", "true", "Tail connects to head"), ex("head = [1], pos = -1", "false", "No cycle")], ["Node count <= 10^4"]),
    q("Binary Search", "Search for target in sorted array. Return index or -1.", "Binary Search", "Easy",
      [ex("nums = [-1,0,3,5,9,12], target = 9", "4"), ex("nums = [-1,0,3,5,9,12], target = 2", "-1"), ex("nums = [5], target = 5", "0")], ["1 <= nums.length <= 10^4"]),
    q("Move Zeroes", "Move all 0's to end while maintaining relative order of non-zero elements in-place.", "Arrays & Two Pointers", "Easy",
      [ex("nums = [0,1,0,3,12]", "[1,3,12,0,0]"), ex("nums = [0]", "[0]"), ex("nums = [1,0,2]", "[1,2,0]")], ["1 <= nums.length <= 10^4"]),
    q("Contains Duplicate", "Return true if any value appears at least twice.", "Hash Maps", "Easy",
      [ex("nums = [1,2,3,1]", "true"), ex("nums = [1,2,3,4]", "false"), ex("nums = [1,1,1,3,3,4,3,2,4,2]", "true")], ["1 <= nums.length <= 10^5"]),
    q("Roman to Integer", "Convert roman numeral string to integer.", "Hash Maps & Strings", "Easy",
      [ex("s = 'III'", "3"), ex("s = 'LVIII'", "58"), ex("s = 'MCMXCIV'", "1994")], ["1 <= s.length <= 15"]),
    q("Palindrome Number", "Check if integer reads the same backward.", "Math", "Easy",
      [ex("x = 121", "true"), ex("x = -121", "false"), ex("x = 10", "false")], ["-2^31 <= x <= 2^31 - 1"]),
    q("Intersection of Two Arrays II", "Return intersection with duplicates.", "Hash Maps & Sorting", "Easy",
      [ex("nums1 = [1,2,2,1], nums2 = [2,2]", "[2,2]"), ex("nums1 = [4,9,5], nums2 = [9,4,9,8,4]", "[4,9]"), ex("nums1 = [1], nums2 = [1]", "[1]")], ["1 <= length <= 1000"]),
    q("Longest Substring Without Repeating Characters", "Find length of longest substring without repeating characters.", "Sliding Window", "Medium",
      [ex("s = 'abcabcbb'", "3", "'abc'"), ex("s = 'bbbbb'", "1", "'b'"), ex("s = 'pwwkew'", "3", "'wke'")], ["0 <= s.length <= 5*10^4"]),
    q("3Sum", "Return all triplets that sum to zero, no duplicates.", "Arrays & Two Pointers", "Medium",
      [ex("nums = [-1,0,1,2,-1,-4]", "[[-1,-1,2],[-1,0,1]]"), ex("nums = [0,1,1]", "[]"), ex("nums = [0,0,0]", "[[0,0,0]]")], ["3 <= nums.length <= 3000"]),
    q("Container With Most Water", "Find two lines forming container with most water.", "Two Pointers", "Medium",
      [ex("height = [1,8,6,2,5,4,8,3,7]", "49"), ex("height = [1,1]", "1"), ex("height = [4,3,2,1,4]", "16")], ["2 <= n <= 10^5"]),
    q("Number of Islands", "Count islands in a 2D grid of '1's (land) and '0's (water).", "Graphs & DFS/BFS", "Medium",
      [ex("grid = [['1','1','0'],['1','1','0'],['0','0','1']]", "2"), ex("grid = [['1','1','1'],['0','1','0'],['1','1','1']]", "1"), ex("grid = [['0','0'],['0','0']]", "0")], ["1 <= m, n <= 300"]),
    q("Product of Array Except Self", "Return array where each element is product of all others. No division, O(n) time.", "Arrays & Prefix Products", "Medium",
      [ex("nums = [1,2,3,4]", "[24,12,8,6]"), ex("nums = [-1,1,0,-3,3]", "[0,0,9,0,0]"), ex("nums = [2,3]", "[3,2]")], ["2 <= nums.length <= 10^5"]),
    q("Group Anagrams", "Group strings that are anagrams of each other.", "Hash Maps & Sorting", "Medium",
      [ex("strs = ['eat','tea','tan','ate','nat','bat']", "[['bat'],['nat','tan'],['ate','eat','tea']]"), ex("strs = ['']", "[['']]"), ex("strs = ['a']", "[['a']]")], ["1 <= strs.length <= 10^4"]),
    q("Coin Change", "Find fewest coins needed to make amount. Return -1 if impossible.", "Dynamic Programming", "Medium",
      [ex("coins = [1,5,10,25], amount = 30", "2", "25 + 5"), ex("coins = [2], amount = 3", "-1", "Not possible"), ex("coins = [1], amount = 0", "0", "No coins needed")], ["1 <= coins.length <= 12"]),
    q("Binary Tree Level Order Traversal", "Return level order traversal of binary tree nodes' values.", "Trees & BFS", "Medium",
      [ex("root = [3,9,20,null,null,15,7]", "[[3],[9,20],[15,7]]"), ex("root = [1]", "[[1]]"), ex("root = []", "[]")], ["Node count <= 2000"]),
    q("Course Schedule", "Determine if you can finish all courses given prerequisites (detect cycle).", "Graphs & Topological Sort", "Medium",
      [ex("numCourses = 2, prerequisites = [[1,0]]", "true"), ex("numCourses = 2, prerequisites = [[1,0],[0,1]]", "false"), ex("numCourses = 1, prerequisites = []", "true")], ["1 <= numCourses <= 2000"]),
    q("Validate Binary Search Tree", "Determine if a binary tree is a valid BST.", "Trees & DFS", "Medium",
      [ex("root = [2,1,3]", "true"), ex("root = [5,1,4,null,null,3,6]", "false"), ex("root = [1]", "true")], ["Node count <= 10^4"]),
    q("Longest Palindromic Substring", "Return the longest palindromic substring.", "Dynamic Programming & Strings", "Medium",
      [ex("s = 'babad'", "'bab'", "'aba' also valid"), ex("s = 'cbbd'", "'bb'"), ex("s = 'a'", "'a'")], ["1 <= s.length <= 1000"]),
    q("Search in Rotated Sorted Array", "Search target in rotated sorted array in O(log n).", "Binary Search", "Medium",
      [ex("nums = [4,5,6,7,0,1,2], target = 0", "4"), ex("nums = [4,5,6,7,0,1,2], target = 3", "-1"), ex("nums = [1], target = 0", "-1")], ["1 <= nums.length <= 5000"]),
    q("Top K Frequent Elements", "Return the k most frequent elements.", "Hash Maps & Heaps", "Medium",
      [ex("nums = [1,1,1,2,2,3], k = 2", "[1,2]"), ex("nums = [1], k = 1", "[1]"), ex("nums = [4,4,4,2,2,1], k = 1", "[4]")], ["1 <= nums.length <= 10^5"]),
    q("Merge Intervals", "Merge all overlapping intervals.", "Sorting & Intervals", "Medium",
      [ex("intervals = [[1,3],[2,6],[8,10],[15,18]]", "[[1,6],[8,10],[15,18]]"), ex("intervals = [[1,4],[4,5]]", "[[1,5]]"), ex("intervals = [[1,4],[0,4]]", "[[0,4]]")], ["1 <= intervals.length <= 10^4"]),
    q("Word Search", "Find if word exists in grid via adjacent cells.", "Backtracking & DFS", "Medium",
      [ex("board = [['A','B'],['C','D']], word = 'ABDC'", "true"), ex("board = [['A','B'],['C','D']], word = 'ABCD'", "false"), ex("board = [['a']], word = 'a'", "true")], ["1 <= m, n <= 6"]),
    q("Rotate Image", "Rotate n x n matrix 90 degrees clockwise in-place.", "Matrix & Math", "Medium",
      [ex("matrix = [[1,2,3],[4,5,6],[7,8,9]]", "[[7,4,1],[8,5,2],[9,6,3]]"), ex("matrix = [[1,2],[3,4]]", "[[3,1],[4,2]]"), ex("matrix = [[1]]", "[[1]]")], ["1 <= n <= 20"]),
    q("Median of Two Sorted Arrays", "Find median of two sorted arrays in O(log(m+n)).", "Binary Search & Divide and Conquer", "Hard",
      [ex("nums1 = [1,3], nums2 = [2]", "2.0"), ex("nums1 = [1,2], nums2 = [3,4]", "2.5"), ex("nums1 = [], nums2 = [1]", "1.0")], ["0 <= m, n <= 1000"]),
    q("Trapping Rain Water", "Compute how much water can be trapped between bars.", "Two Pointers & Stacks", "Hard",
      [ex("height = [0,1,0,2,1,0,1,3,2,1,2,1]", "6"), ex("height = [4,2,0,3,2,5]", "9"), ex("height = [1,0,1]", "1")], ["1 <= n <= 2*10^4"]),
    q("Merge K Sorted Lists", "Merge k sorted linked lists into one sorted list.", "Heaps & Linked Lists", "Hard",
      [ex("lists = [[1,4,5],[1,3,4],[2,6]]", "[1,1,2,3,4,4,5,6]"), ex("lists = []", "[]"), ex("lists = [[]]", "[]")], ["0 <= k <= 10^4"]),
    q("Minimum Window Substring", "Find smallest window in s containing all chars of t.", "Sliding Window", "Hard",
      [ex("s = 'ADOBECODEBANC', t = 'ABC'", "'BANC'"), ex("s = 'a', t = 'a'", "'a'"), ex("s = 'a', t = 'aa'", "''")], ["1 <= s.length, t.length <= 10^5"]),
    q("Word Ladder", "Find shortest transformation sequence changing one letter at a time.", "Graphs & BFS", "Hard",
      [ex("beginWord = 'hit', endWord = 'cog', list = ['hot','dot','dog','lot','log','cog']", "5"), ex("beginWord = 'hit', endWord = 'cog', list = ['hot','dot','dog','lot','log']", "0"), ex("beginWord = 'a', endWord = 'c', list = ['a','b','c']", "2")], ["1 <= beginWord.length <= 10"]),
    q("Serialize and Deserialize Binary Tree", "Design algorithm to serialize/deserialize a binary tree.", "Trees & Design", "Hard",
      [ex("root = [1,2,3,null,null,4,5]", "[1,2,3,null,null,4,5]"), ex("root = []", "[]"), ex("root = [1]", "[1]")], ["Node count <= 10^4"]),
    q("Longest Increasing Subsequence", "Find length of longest strictly increasing subsequence.", "Dynamic Programming & Binary Search", "Hard",
      [ex("nums = [10,9,2,5,3,7,101,18]", "4", "[2,3,7,101]"), ex("nums = [0,1,0,3,2,3]", "4"), ex("nums = [7,7,7,7]", "1")], ["1 <= nums.length <= 2500"]),
    q("Edit Distance", "Min operations (insert/delete/replace) to convert word1 to word2.", "Dynamic Programming", "Hard",
      [ex("word1 = 'horse', word2 = 'ros'", "3"), ex("word1 = 'intention', word2 = 'execution'", "5"), ex("word1 = '', word2 = 'a'", "1")], ["0 <= length <= 500"]),
    q("LRU Cache", "Design LRU cache with get and put in O(1).", "Hash Maps & Doubly Linked Lists", "Hard",
      [ex("LRUCache(2), put(1,1), put(2,2), get(1)", "1", "Key 1 is accessed"), ex("LRUCache(1), put(1,1), put(2,2), get(1)", "-1", "Key 1 evicted"), ex("LRUCache(2), put(1,1), get(1), put(2,2)", "1", "Key 1 recently used")], ["1 <= capacity <= 3000"]),
    q("Maximum Path Sum in Binary Tree", "Find maximum path sum in binary tree (path doesn't need to pass through root).", "Trees & DFS", "Hard",
      [ex("root = [-10,9,20,null,null,15,7]", "42", "15 -> 20 -> 7"), ex("root = [1,2,3]", "6"), ex("root = [-3]", "-3")], ["Node count <= 3*10^4"]),
    q("Regular Expression Matching", "Implement regex matching with '.' and '*' support.", "Dynamic Programming", "Hard",
      [ex("s = 'aab', p = 'c*a*b'", "true"), ex("s = 'aa', p = 'a'", "false"), ex("s = 'ab', p = '.*'", "true")], ["1 <= s.length, p.length <= 20"]),
    q("Largest Rectangle in Histogram", "Find area of largest rectangle fitting in histogram.", "Stacks & Monotonic Stack", "Hard",
      [ex("heights = [2,1,5,6,2,3]", "10"), ex("heights = [2,4]", "4"), ex("heights = [1]", "1")], ["1 <= heights.length <= 10^5"]),
    q("Alien Dictionary", "Derive character order from sorted alien language words.", "Graphs & Topological Sort", "Hard",
      [ex("words = ['wrt','wrf','er','ett','rftt']", "'wertf'"), ex("words = ['z','x']", "'zx'"), ex("words = ['z','x','z']", "''", "Invalid order")], ["1 <= words.length <= 100"]),
    q("Find Median from Data Stream", "Design data structure supporting addNum and findMedian.", "Heaps & Design", "Hard",
      [ex("addNum(1), addNum(2), findMedian()", "1.5"), ex("addNum(1), findMedian()", "1.0"), ex("addNum(1), addNum(2), addNum(3), findMedian()", "2.0")], ["-10^5 <= num <= 10^5"]),
    q("Longest Valid Parentheses", "Find length of longest valid parentheses substring.", "Dynamic Programming & Stacks", "Hard",
      [ex("s = '(()'", "2"), ex("s = ')()())'", "4"), ex("s = ''", "0")], ["0 <= s.length <= 3*10^4"]),
    q("Word Break II", "Add spaces in string s to form valid sentences from dictionary. Return all possibilities.", "DP & Backtracking", "Hard",
      [ex("s = 'catsanddog', dict = ['cat','cats','and','sand','dog']", "['cats and dog','cat sand dog']"), ex("s = 'pineapplepenapple', dict = ['apple','pen','applepen','pine','pineapple']", "['pine apple pen apple','pineapple pen apple','pine applepen apple']"), ex("s = 'a', dict = ['a']", "['a']")], ["1 <= s.length <= 20"]),
    q("Sliding Window Maximum", "Return max values in each sliding window of size k.", "Deque & Sliding Window", "Hard",
      [ex("nums = [1,3,-1,-3,5,3,6,7], k = 3", "[3,3,5,5,6,7]"), ex("nums = [1], k = 1", "[1]"), ex("nums = [1,-1], k = 1", "[1,-1]")], ["1 <= nums.length <= 10^5"]),
]

AMAZON = [
    q("Two Sum", "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.", "Arrays & Hash Maps", "Easy",
      [ex("nums = [2,7,11,15], target = 9", "[0,1]"), ex("nums = [3,2,4], target = 6", "[1,2]"), ex("nums = [3,3], target = 6", "[0,1]")], ["2 <= nums.length <= 10^4"]),
    q("Valid Parentheses", "Determine if string of brackets is valid.", "Stacks", "Easy",
      [ex("s = '([])'", "true"), ex("s = '(]'", "false"), ex("s = '{}'", "true")], ["1 <= s.length <= 10^4"]),
    q("Merge Two Sorted Lists", "Merge two sorted linked lists.", "Linked Lists", "Easy",
      [ex("l1 = [1,2,4], l2 = [1,3,4]", "[1,1,2,3,4,4]"), ex("l1 = [], l2 = []", "[]"), ex("l1 = [], l2 = [0]", "[0]")], ["0 <= list length <= 50"]),
    q("Best Time to Buy and Sell Stock", "Find max profit from one buy-sell transaction.", "Arrays & Greedy", "Easy",
      [ex("prices = [7,1,5,3,6,4]", "5"), ex("prices = [7,6,4,3,1]", "0"), ex("prices = [2,4,1]", "2")], ["1 <= prices.length <= 10^5"]),
    q("Reverse Linked List", "Reverse a singly linked list.", "Linked Lists", "Easy",
      [ex("head = [1,2,3,4,5]", "[5,4,3,2,1]"), ex("head = [1,2]", "[2,1]"), ex("head = []", "[]")], ["0 <= nodes <= 5000"]),
    q("Maximum Subarray", "Find contiguous subarray with largest sum.", "Dynamic Programming", "Easy",
      [ex("nums = [-2,1,-3,4,-1,2,1,-5,4]", "6"), ex("nums = [1]", "1"), ex("nums = [5,4,-1,7,8]", "23")], ["1 <= nums.length <= 10^5"]),
    q("Valid Anagram", "Return true if t is an anagram of s.", "Hash Maps & Sorting", "Easy",
      [ex("s = 'anagram', t = 'nagaram'", "true"), ex("s = 'rat', t = 'car'", "false"), ex("s = 'a', t = 'a'", "true")], ["1 <= s.length <= 5*10^4"]),
    q("Climbing Stairs", "How many distinct ways to climb n stairs (1 or 2 steps at a time)?", "Dynamic Programming", "Easy",
      [ex("n = 2", "2"), ex("n = 3", "3"), ex("n = 4", "5")], ["1 <= n <= 45"]),
    q("Contains Duplicate", "Return true if any value appears at least twice.", "Hash Maps", "Easy",
      [ex("nums = [1,2,3,1]", "true"), ex("nums = [1,2,3,4]", "false"), ex("nums = [1,1,1,3,3,4,3,2,4,2]", "true")], ["1 <= nums.length <= 10^5"]),
    q("Binary Search", "Search target in sorted array, return index or -1.", "Binary Search", "Easy",
      [ex("nums = [-1,0,3,5,9,12], target = 9", "4"), ex("nums = [-1,0,3,5,9,12], target = 2", "-1"), ex("nums = [5], target = 5", "0")], ["1 <= nums.length <= 10^4"]),
    q("Linked List Cycle", "Determine if linked list has a cycle.", "Linked Lists & Two Pointers", "Easy",
      [ex("head = [3,2,0,-4], pos = 1", "true"), ex("head = [1,2], pos = 0", "true"), ex("head = [1], pos = -1", "false")], ["Node count <= 10^4"]),
    q("Maximum Depth of Binary Tree", "Return maximum depth of binary tree.", "Trees & DFS", "Easy",
      [ex("root = [3,9,20,null,null,15,7]", "3"), ex("root = [1,null,2]", "2"), ex("root = []", "0")], ["Node count <= 10^4"]),
    q("Fizz Buzz", "Return array with FizzBuzz rules applied.", "Math & Strings", "Easy",
      [ex("n = 3", "['1','2','Fizz']"), ex("n = 5", "['1','2','Fizz','4','Buzz']"), ex("n = 15", "['1','2','Fizz','4','Buzz','Fizz','7','8','Fizz','Buzz','11','Fizz','13','14','FizzBuzz']")], ["1 <= n <= 10^4"]),
    q("Min Stack", "Design stack that supports push, pop, top, and getMin in O(1).", "Stacks & Design", "Easy",
      [ex("MinStack(), push(-2), push(0), push(-3), getMin()", "-3"), ex("MinStack(), push(1), push(2), top()", "2"), ex("MinStack(), push(0), push(1), pop(), getMin()", "0")], ["Methods called at most 3*10^4 times"]),
    q("Subtree of Another Tree", "Check if tree t is a subtree of tree s.", "Trees & DFS", "Easy",
      [ex("s = [3,4,5,1,2], t = [4,1,2]", "true"), ex("s = [3,4,5,1,2,null,null,null,null,0], t = [4,1,2]", "false"), ex("s = [1,1], t = [1]", "true")], ["Node count <= 2000"]),
    q("Diameter of Binary Tree", "Find the diameter (longest path between any two nodes) of a binary tree.", "Trees & DFS", "Easy",
      [ex("root = [1,2,3,4,5]", "3", "Path 4->2->1->3"), ex("root = [1,2]", "1"), ex("root = [1]", "0")], ["Node count <= 10^4"]),
    q("Missing Number", "Given array containing n distinct numbers from 0 to n, find the missing one.", "Bit Manipulation & Math", "Easy",
      [ex("nums = [3,0,1]", "2"), ex("nums = [0,1]", "2"), ex("nums = [9,6,4,2,3,5,7,0,1]", "8")], ["n == nums.length", "0 <= nums[i] <= n"]),
    q("Number of Islands", "Count islands in 2D grid.", "Graphs & DFS/BFS", "Medium",
      [ex("grid = [['1','1','0'],['1','1','0'],['0','0','1']]", "2"), ex("grid = [['1','1','1'],['0','1','0'],['1','1','1']]", "1"), ex("grid = [['0','0'],['0','0']]", "0")], ["1 <= m, n <= 300"]),
    q("Longest Substring Without Repeating Characters", "Find length of longest substring without repeating characters.", "Sliding Window", "Medium",
      [ex("s = 'abcabcbb'", "3"), ex("s = 'bbbbb'", "1"), ex("s = 'pwwkew'", "3")], ["0 <= s.length <= 5*10^4"]),
    q("3Sum", "Find all unique triplets summing to zero.", "Arrays & Two Pointers", "Medium",
      [ex("nums = [-1,0,1,2,-1,-4]", "[[-1,-1,2],[-1,0,1]]"), ex("nums = [0,1,1]", "[]"), ex("nums = [0,0,0]", "[[0,0,0]]")], ["3 <= nums.length <= 3000"]),
    q("Product of Array Except Self", "Each element equals product of all others. No division.", "Arrays & Prefix Products", "Medium",
      [ex("nums = [1,2,3,4]", "[24,12,8,6]"), ex("nums = [-1,1,0,-3,3]", "[0,0,9,0,0]"), ex("nums = [2,3]", "[3,2]")], ["2 <= nums.length <= 10^5"]),
    q("Group Anagrams", "Group strings that are anagrams.", "Hash Maps & Sorting", "Medium",
      [ex("strs = ['eat','tea','tan','ate','nat','bat']", "[['bat'],['nat','tan'],['ate','eat','tea']]"), ex("strs = ['']", "[['']]"), ex("strs = ['a']", "[['a']]")], ["1 <= strs.length <= 10^4"]),
    q("Merge Intervals", "Merge all overlapping intervals.", "Sorting & Intervals", "Medium",
      [ex("intervals = [[1,3],[2,6],[8,10]]", "[[1,6],[8,10]]"), ex("intervals = [[1,4],[4,5]]", "[[1,5]]"), ex("intervals = [[1,4],[0,4]]", "[[0,4]]")], ["1 <= intervals.length <= 10^4"]),
    q("Binary Tree Level Order Traversal", "Level order traversal of binary tree.", "Trees & BFS", "Medium",
      [ex("root = [3,9,20,null,null,15,7]", "[[3],[9,20],[15,7]]"), ex("root = [1]", "[[1]]"), ex("root = []", "[]")], ["Node count <= 2000"]),
    q("Course Schedule", "Can you finish all courses given prerequisites?", "Graphs & Topological Sort", "Medium",
      [ex("numCourses = 2, prerequisites = [[1,0]]", "true"), ex("numCourses = 2, prerequisites = [[1,0],[0,1]]", "false"), ex("numCourses = 1, prerequisites = []", "true")], ["1 <= numCourses <= 2000"]),
    q("Coin Change", "Fewest coins to make amount.", "Dynamic Programming", "Medium",
      [ex("coins = [1,5,10,25], amount = 30", "2"), ex("coins = [2], amount = 3", "-1"), ex("coins = [1], amount = 0", "0")], ["1 <= coins.length <= 12"]),
    q("Validate Binary Search Tree", "Is this binary tree a valid BST?", "Trees & DFS", "Medium",
      [ex("root = [2,1,3]", "true"), ex("root = [5,1,4,null,null,3,6]", "false"), ex("root = [1]", "true")], ["Node count <= 10^4"]),
    q("Search in Rotated Sorted Array", "Search in rotated sorted array O(log n).", "Binary Search", "Medium",
      [ex("nums = [4,5,6,7,0,1,2], target = 0", "4"), ex("nums = [4,5,6,7,0,1,2], target = 3", "-1"), ex("nums = [1], target = 0", "-1")], ["1 <= nums.length <= 5000"]),
    q("Word Break", "Can string s be segmented into dictionary words?", "Dynamic Programming", "Medium",
      [ex("s = 'leetcode', wordDict = ['leet','code']", "true"), ex("s = 'applepenapple', wordDict = ['apple','pen']", "true"), ex("s = 'catsandog', wordDict = ['cats','dog','sand','and','cat']", "false")], ["1 <= s.length <= 300"]),
    q("Top K Frequent Elements", "Return k most frequent elements.", "Hash Maps & Heaps", "Medium",
      [ex("nums = [1,1,1,2,2,3], k = 2", "[1,2]"), ex("nums = [1], k = 1", "[1]"), ex("nums = [4,4,4,2,2,1], k = 1", "[4]")], ["1 <= nums.length <= 10^5"]),
    q("Kth Smallest Element in BST", "Return kth smallest value in BST.", "Trees & In-order Traversal", "Medium",
      [ex("root = [3,1,4,null,2], k = 1", "1"), ex("root = [5,3,6,2,4,null,null,1], k = 3", "3"), ex("root = [1], k = 1", "1")], ["1 <= k <= n"]),
    q("Longest Palindromic Substring", "Return longest palindromic substring.", "DP & Strings", "Medium",
      [ex("s = 'babad'", "'bab'"), ex("s = 'cbbd'", "'bb'"), ex("s = 'a'", "'a'")], ["1 <= s.length <= 1000"]),
    q("Spiral Matrix", "Return all elements in spiral order.", "Matrix & Simulation", "Medium",
      [ex("matrix = [[1,2,3],[4,5,6],[7,8,9]]", "[1,2,3,6,9,8,7,4,5]"), ex("matrix = [[1,2],[3,4]]", "[1,2,4,3]"), ex("matrix = [[1]]", "[1]")], ["1 <= m, n <= 10"]),
    q("Rotate Image", "Rotate matrix 90 degrees clockwise in-place.", "Matrix & Math", "Medium",
      [ex("matrix = [[1,2,3],[4,5,6],[7,8,9]]", "[[7,4,1],[8,5,2],[9,6,3]]"), ex("matrix = [[1,2],[3,4]]", "[[3,1],[4,2]]"), ex("matrix = [[1]]", "[[1]]")], ["1 <= n <= 20"]),
    q("Trapping Rain Water", "How much water can be trapped between bars?", "Two Pointers & Stacks", "Hard",
      [ex("height = [0,1,0,2,1,0,1,3,2,1,2,1]", "6"), ex("height = [4,2,0,3,2,5]", "9"), ex("height = [1,0,1]", "1")], ["1 <= n <= 2*10^4"]),
    q("Merge K Sorted Lists", "Merge k sorted linked lists.", "Heaps & Linked Lists", "Hard",
      [ex("lists = [[1,4,5],[1,3,4],[2,6]]", "[1,1,2,3,4,4,5,6]"), ex("lists = []", "[]"), ex("lists = [[]]", "[]")], ["0 <= k <= 10^4"]),
    q("LRU Cache", "Design LRU cache with O(1) get and put.", "Hash Maps & Doubly Linked Lists", "Hard",
      [ex("LRUCache(2), put(1,1), put(2,2), get(1)", "1"), ex("LRUCache(1), put(1,1), put(2,2), get(1)", "-1"), ex("LRUCache(2), get(2)", "-1")], ["1 <= capacity <= 3000"]),
    q("Word Ladder", "Shortest transformation sequence changing one letter at a time.", "Graphs & BFS", "Hard",
      [ex("beginWord = 'hit', endWord = 'cog'", "5"), ex("beginWord = 'hit', endWord = 'cog', list = ['hot','dot','dog','lot','log']", "0"), ex("beginWord = 'a', endWord = 'c', list = ['a','b','c']", "2")], ["1 <= beginWord.length <= 10"]),
    q("Minimum Window Substring", "Smallest window in s containing all chars of t.", "Sliding Window", "Hard",
      [ex("s = 'ADOBECODEBANC', t = 'ABC'", "'BANC'"), ex("s = 'a', t = 'a'", "'a'"), ex("s = 'a', t = 'aa'", "''")], ["1 <= s.length, t.length <= 10^5"]),
    q("Median of Two Sorted Arrays", "Find median of two sorted arrays O(log(m+n)).", "Binary Search", "Hard",
      [ex("nums1 = [1,3], nums2 = [2]", "2.0"), ex("nums1 = [1,2], nums2 = [3,4]", "2.5"), ex("nums1 = [], nums2 = [1]", "1.0")], ["0 <= m, n <= 1000"]),
    q("Serialize and Deserialize Binary Tree", "Design serialization/deserialization for binary tree.", "Trees & Design", "Hard",
      [ex("root = [1,2,3,null,null,4,5]", "[1,2,3,null,null,4,5]"), ex("root = []", "[]"), ex("root = [1]", "[1]")], ["Node count <= 10^4"]),
    q("Find Median from Data Stream", "Design data structure for streaming median.", "Heaps & Design", "Hard",
      [ex("addNum(1), addNum(2), findMedian()", "1.5"), ex("addNum(1), findMedian()", "1.0"), ex("addNum(1), addNum(2), addNum(3), findMedian()", "2.0")], ["-10^5 <= num <= 10^5"]),
    q("Maximum Path Sum in Binary Tree", "Find max path sum in binary tree.", "Trees & DFS", "Hard",
      [ex("root = [-10,9,20,null,null,15,7]", "42"), ex("root = [1,2,3]", "6"), ex("root = [-3]", "-3")], ["Node count <= 3*10^4"]),
    q("Largest Rectangle in Histogram", "Largest rectangle area in histogram.", "Stacks & Monotonic Stack", "Hard",
      [ex("heights = [2,1,5,6,2,3]", "10"), ex("heights = [2,4]", "4"), ex("heights = [1]", "1")], ["1 <= heights.length <= 10^5"]),
    q("Sliding Window Maximum", "Max values in each sliding window of size k.", "Deque & Sliding Window", "Hard",
      [ex("nums = [1,3,-1,-3,5,3,6,7], k = 3", "[3,3,5,5,6,7]"), ex("nums = [1], k = 1", "[1]"), ex("nums = [1,-1], k = 1", "[1,-1]")], ["1 <= nums.length <= 10^5"]),
    q("Critical Connections in a Network", "Find all critical connections (bridges) in a network graph.", "Graphs & Tarjan's Algorithm", "Hard",
      [ex("n = 4, connections = [[0,1],[1,2],[2,0],[1,3]]", "[[1,3]]"), ex("n = 2, connections = [[0,1]]", "[[0,1]]"), ex("n = 3, connections = [[0,1],[1,2],[2,0]]", "[]")], ["2 <= n <= 10^5"]),
    q("Longest Increasing Subsequence", "Length of longest strictly increasing subsequence.", "DP & Binary Search", "Hard",
      [ex("nums = [10,9,2,5,3,7,101,18]", "4"), ex("nums = [0,1,0,3,2,3]", "4"), ex("nums = [7,7,7,7]", "1")], ["1 <= nums.length <= 2500"]),
    q("Word Break II", "All ways to segment string into dictionary words.", "DP & Backtracking", "Hard",
      [ex("s = 'catsanddog'", "['cats and dog','cat sand dog']"), ex("s = 'a', dict = ['a']", "['a']"), ex("s = 'ab', dict = ['a','b']", "['a b']")], ["1 <= s.length <= 20"]),
    q("Edit Distance", "Min edit operations to convert word1 to word2.", "Dynamic Programming", "Hard",
      [ex("word1 = 'horse', word2 = 'ros'", "3"), ex("word1 = 'intention', word2 = 'execution'", "5"), ex("word1 = '', word2 = 'a'", "1")], ["0 <= length <= 500"]),
    q("Regular Expression Matching", "Regex matching with '.' and '*'.", "Dynamic Programming", "Hard",
      [ex("s = 'aab', p = 'c*a*b'", "true"), ex("s = 'aa', p = 'a'", "false"), ex("s = 'ab', p = '.*'", "true")], ["1 <= s.length, p.length <= 20"]),
]


def make_company_variant(base, company_name, swaps=None):
    result = copy.deepcopy(base)
    for q_item in result:
        q_item["company"] = company_name
    if swaps:
        for idx, new_q in swaps:
            if idx < len(result):
                new_q["company"] = company_name
                result[idx] = new_q
    return result

META_SWAPS = [
    (14, q("Reverse String", "Reverse a string in-place as array of characters.", "Arrays & Two Pointers", "Easy",
           [ex("s = ['h','e','l','l','o']", "['o','l','l','e','h']"), ex("s = ['H','a','n','n','a','h']", "['h','a','n','n','a','H']"), ex("s = ['a']", "['a']")], ["1 <= s.length <= 10^5"])),
    (15, q("Minimum Remove to Make Valid Parentheses", "Remove minimum parentheses to make string valid.", "Stacks & Strings", "Medium",
           [ex("s = 'lee(t(c)o)de)'", "'lee(t(c)o)de'"), ex("s = 'a)b(c)d'", "'ab(c)d'"), ex("s = '))(('", "''")], ["1 <= s.length <= 10^5"])),
    (47, q("Verifying an Alien Dictionary", "Given words sorted in alien order, verify if they are sorted.", "Hash Maps", "Easy",
           [ex("words = ['hello','leetcode'], order = 'hlabcdefgijkmnopqrstuvwxyz'", "true"), ex("words = ['word','world','row'], order = 'worldabcefghijkmnpqstuvxyz'", "false"), ex("words = ['apple','app'], order = 'abcdefghijklmnopqrstuvwxyz'", "false")], ["1 <= words.length <= 100"])),
]

APPLE_SWAPS = [
    (13, q("First Unique Character in String", "Find first non-repeating character and return its index.", "Hash Maps & Strings", "Easy",
           [ex("s = 'leetcode'", "0", "'l' is first unique"), ex("s = 'loveleetcode'", "2", "'v' is first unique"), ex("s = 'aabb'", "-1", "No unique character")], ["1 <= s.length <= 10^5"])),
    (16, q("Power of Two", "Check if n is a power of two.", "Bit Manipulation", "Easy",
           [ex("n = 1", "true"), ex("n = 16", "true"), ex("n = 3", "false")], ["-2^31 <= n <= 2^31 - 1"])),
]

NETFLIX_SWAPS = [
    (14, q("Implement Queue using Stacks", "Implement FIFO queue using two stacks.", "Stacks & Design", "Easy",
           [ex("push(1), push(2), peek() -> 1, pop() -> 1", "1, 1"), ex("push(1), pop() -> 1, empty() -> true", "1, true"), ex("push(3), push(4), peek() -> 3", "3")], ["1 <= x <= 9"])),
    (15, q("Range Sum Query - Immutable", "Given array, find sum of elements between indices i and j.", "Prefix Sum", "Easy",
           [ex("nums = [-2,0,3,-5,2,-1], sumRange(0,2)", "1"), ex("nums = [-2,0,3,-5,2,-1], sumRange(2,5)", "-1"), ex("nums = [-2,0,3,-5,2,-1], sumRange(0,5)", "-3")], ["1 <= nums.length <= 10^4"])),
]

MICROSOFT_SWAPS = [
    (13, q("Excel Sheet Column Number", "Convert Excel column title to number (A=1, B=2...Z=26, AA=27).", "Math & Strings", "Easy",
           [ex("columnTitle = 'A'", "1"), ex("columnTitle = 'AB'", "28"), ex("columnTitle = 'ZY'", "701")], ["1 <= columnTitle.length <= 7"])),
    (15, q("Reverse Bits", "Reverse bits of a 32-bit unsigned integer.", "Bit Manipulation", "Easy",
           [ex("n = 00000010100101000001111010011100", "964176192"), ex("n = 11111111111111111111111111111101", "3221225471"), ex("n = 00000000000000000000000000000001", "2147483648")], ["Input is a 32-bit unsigned integer"])),
]

STARTUP_SWAPS = [
    (14, q("Implement Stack using Queues", "Implement LIFO stack using two queues.", "Queues & Design", "Easy",
           [ex("push(1), push(2), top() -> 2, pop() -> 2", "2, 2"), ex("push(1), pop() -> 1, empty() -> true", "1, true"), ex("push(3), push(4), top() -> 4", "4")], ["1 <= x <= 9"])),
    (16, q("Happy Number", "Determine if a number is happy (sum of squares of digits eventually equals 1).", "Math & Hash Maps", "Easy",
           [ex("n = 19", "true", "1^2+9^2=82, 8^2+2^2=68, 6^2+8^2=100, 1"), ex("n = 2", "false"), ex("n = 7", "true")], ["1 <= n <= 2^31 - 1"])),
]


def assign_ids(questions, company):
    for i, q_item in enumerate(questions):
        q_item["id"] = f"{company.lower().replace(' ', '_')}_{i+1:03d}"
        q_item["company"] = company
    return questions


def main():
    META = make_company_variant(GOOGLE, "Meta", META_SWAPS)
    APPLE = make_company_variant(GOOGLE, "Apple", APPLE_SWAPS)
    NETFLIX = make_company_variant(GOOGLE, "Netflix", NETFLIX_SWAPS)
    MICROSOFT = make_company_variant(GOOGLE, "Microsoft", MICROSOFT_SWAPS)
    STARTUP = make_company_variant(GOOGLE, "Startup", STARTUP_SWAPS)

    all_questions = {
        "Google": assign_ids(GOOGLE, "Google"),
        "Amazon": assign_ids(AMAZON, "Amazon"),
        "Meta": assign_ids(META, "Meta"),
        "Apple": assign_ids(APPLE, "Apple"),
        "Netflix": assign_ids(NETFLIX, "Netflix"),
        "Microsoft": assign_ids(MICROSOFT, "Microsoft"),
        "Startup": assign_ids(STARTUP, "Startup"),
    }

    total = 0
    for company, qs in all_questions.items():
        easy = sum(1 for x in qs if x["difficulty"] == "Easy")
        med = sum(1 for x in qs if x["difficulty"] == "Medium")
        hard = sum(1 for x in qs if x["difficulty"] == "Hard")
        total += len(qs)
        print(f"{company}: {len(qs)} questions (Easy: {easy}, Medium: {med}, Hard: {hard})")

    print(f"\nPushing {total} questions to Firebase Firestore...\n")

    success = 0
    for company, questions in all_questions.items():
        if push_company(company, questions):
            success += 1

    print(f"\nDone! {success}/{len(all_questions)} companies pushed successfully.")


if __name__ == "__main__":
    main()
