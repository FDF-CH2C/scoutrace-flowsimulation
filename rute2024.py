"""
Setup course - insert own course here!
Activity: capacity, min, max, name
"""

Post0 = Activity(8, 10, 13, "Startpost")
Post0A = Activity(20, 50, 70, "Post 0A")
Post1 = Activity(5, 10, 15, "Post 1")
Post2 = Activity(5, 10, 15, "Post 2")
Post3 = Activity(5, 10, 15, "Post 3")
Post4 = Activity(5, 10, 15, "Post 4")
Post4A = Activity(5, 10, 15, "Post 4A")
Post5 = Activity(5, 10, 15, "Post 5")
Post6 = Activity(5, 10, 15, "Post 6")
Post7 = Activity(5, 10, 15, "Post 7")
Post7A = Activity(5, 10, 15, "Post 7A")
Post8 = Activity(5, 10, 15, "Post 8")
Post9 = Activity(8, 10, 15, "Post 9")
Post10 = Activity(99, 60, 70, "Mad")
Post11 = Activity(5, 10, 15, "Post 11")
Post12 = Activity(5, 10, 15, "Post 12")
Post13 = Activity(5, 10, 15, "Post 13")
Post14 = Activity(5, 10, 15, "Post 14")
Post15 = Activity(5, 10, 15, "Post 15")
Post16 = Activity(20, 10, 40, "DFO")
PostMaal = Activity(99, None, None, "Mål")

Activities = [Post0, Post0A, Post1, Post2, Post3, Post4, Post4A, Post5, Post6, Post7, Post7A, Post8,
            Post9, Post10, Post11, Post12, Post13, Post14, Post15, Post16, PostMaal]

"""
Link activities [act1, distance1, act2, distance2, ...]
"""
course = {"V": [
            Post0, 1.1,
            Post1, 1.2,
            Post2, 1.7,
            Post3, 1.6,
            Post4, 0.4,
            Post5, 1.7,
            Post6, 1.3,
            Post7, 2,
            Post8, 1.7,
            Post9, 0,
            Post10,1.4,
            Post11,1.1,
            Post12,2.3,
            Post13,1.6,
            Post14,1.8,
            Post15,0.6,
            Post16,1.1,
            PostMaal],
        "S": [Post0, 0.6,
            Post0A,1.7,
            Post1, 1.2,
            Post2, 1.7,
            Post3, 1.6,
            Post4, 0.4,
            Post5, 1.7,
            Post6, 1.3,
            Post7, 1.3,
            Post7A,2.2,
            Post8, 1.7,
            Post9, 0,
            Post10,1.4,
            Post11,1.1,
            Post12,2.3,
            Post13,1.6,
            Post14,1.8,
            Post15,0.6,
            Post16,1.1,
            PostMaal],
        "OB": [
            Post0, 0.6,
            Post0A,1.7,
            Post1, 1.2,
            Post2, 1.7,
            Post3, 1.6,
            Post4, 0.4,
            Post4A,0.8,
            Post5, 1.7,
            Post6, 1.3,
            Post7, 1.3,
            Post7A,2.2,
            Post8, 1.7,
            Post9, 0,
            Post10,1.4,
            Post11,1.1,
            Post12,2.3,
            Post13,1.6,
            Post14,1.8,
            Post15,0.6,
            Post16,1.1,
            PostMaal]}
""" Setup course END """