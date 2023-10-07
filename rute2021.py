"""
Setup course - insert own course here!
Activity: capacity, min, max, name
"""

Post0 = Activity(8, 10, 13, "Startpost")
Post0A = Activity(5, 10, 15, "Post 0A")
Post0B = Activity(5, 10, 15, "Post 0B")
Post0C = Activity(5, 10, 15, "Post 0C")
Post1 = Activity(5, 10, 15, "Post 1")
Post2 = Activity(5, 10, 15, "Post 2")
Post3 = Activity(5, 10, 15, "Post 3")
Post4 = Activity(5, 10, 15, "Post 4")
Post5 = Activity(5, 10, 15, "Post 5")
Post5A = Activity(5, 10, 15, "Post 5A")
Post5B = Activity(99, 5, 10, "Post 5B") # Død post - rundt om grusgraven
Post6 = Activity(5, 10, 15, "Post 6")
PostM = Activity(99, 60, 70, "Mad") # Opgave på madposten. Tager ikke ekstra tid
Post7 = Activity(99, 0, 0, "Post 7")
Post8 = Activity(5, 10, 15, "Post 8")
Post9 = Activity(5, 10, 15, "Post 9")
Post10 = Activity(5, 10, 15, "Post 10")
Post11 = Activity(5, 10, 15, "Post 11")
Post12 = Activity(5, 10, 15, "Post 12")
Post13 = Activity(5, 10, 15, "Post 13")
Post14 = Activity(5, 10, 15, "DFO")
PostMaal = Activity(99, None, None, "Mål")

Activities = [Post0, Post0A, Post0B, Post0C, Post1, Post2, Post3, Post4, Post5, Post5A,
              Post5B, Post6, PostM, Post7, Post8, Post9, Post10, Post11, Post12, Post13, Post14, PostMaal]

"""
Link activities [act1, distance1, act2, distance2, ...]
"""
course = {"V": [Post0, 1.5,
                Post1, 1.2,
                Post2, 1.1,
                Post3, 1.2,
                Post4, 1.0,
                Post5, 2.4,
                Post6, 2.0,
                PostM, 0,
                Post7, 2.0,
                Post8, 2.1,
                Post9, 1.5,
                Post10, 1.4,
                Post11, 1.9,
                Post12, 1.3,
                Post13, 1.6,
                Post14, 1.4,
                PostMaal],
          "S": [Post0, 1.0,
                Post0A, 1.2,
                Post0B, 2.5,
                Post1, 1.2,
                Post2, 1.1,
                Post3, 1.2,
                Post4, 1.0,
                Post5, 2.4,
                Post6, 2.0,
                PostM, 0,
                Post7, 2.0,
                Post8, 2.1,
                Post9, 1.5,
                Post10, 1.4,
                Post11, 1.9,
                Post12, 1.3,
                Post13, 1.6,
                Post14, 1.4,
                PostMaal],
          "OB": [Post0, 1.0,
                Post0A, 1.2,
                Post0B, 2.5,
                Post1, 1.2,
                Post2, 1.1,
                Post3, 1.2,
                Post4, 1.0,
                Post5, 2.5,
                Post5A, 6,
                Post5B, 0,
                Post6, 2.0,
                PostM, 0,
                Post7, 2.0,
                Post8, 2.1,
                Post9, 1.5,
                Post10, 1.4,
                Post11, 1.9,
                Post12, 1.3,
                Post13, 1.6,
                Post14, 1.4,
                PostMaal]}
""" Setup course END """
