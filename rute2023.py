"""
    Setup course - insert own course here!
    Activity: capacity, min, max, name
    """

    Post0 = Activity(8, 10, 13, "Startpost")
    Post0A = Activity(5, 10, 15, "Post 0A")
    Post0B = Activity(5, 10, 15, "Post 0B")
    Post1 = Activity(5, 10, 15, "Post 1")
    Post2 = Activity(7, 20, 25, "Post 2")
    Post3 = Activity(5, 10, 15, "Post 3")
    Post4 = Activity(10, 15, 20, "Post 4")
    Post5 = Activity(5, 15, 20, "Post 5")
    Post5A = Activity(5, 10, 15, "Post 5A")
    Post5B = Activity(5, 10, 15, "Post 5B")
    Post6 = Activity(7, 15, 20, "Post 6")
    Post7 = Activity(5, 10, 15, "Post 7") # Død
    Post8 = Activity(5, 10, 15, "Post 8")
    Post9 = Activity(4, 10, 15, "Post 9") # Klatring
    Post10 = Activity(99, 60, 70, "Mad") # Opgave på madposten. Tager ikke ekstra tid
    Post11 = Activity(5, 10, 15, "Post 11")
    Post12 = Activity(5, 10, 15, "Post 12")
    Post13 = Activity(5, 10, 15, "Post 13")
    Post14 = Activity(5, 10, 15, "Post 14")
    Post15 = Activity(5, 15, 20, "Post 15")
    Post16 = Activity(20, 10, 40, "DFO")
    PostMaal = Activity(99, None, None, "Mål")

    Activities = [Post0, Post0A, Post0B, Post1, Post2, Post3, Post4, Post5, Post5A, Post5B, Post6, Post7, Post8,
                Post9, Post10, Post11, Post12, Post13, Post14, Post15, Post16, PostMaal]

    """
    Link activities [act1, distance1, act2, distance2, ...]
    """
    course = {"V": [
                Post0, 1,
                Post1, 0.7,
                Post2, 0.9,
                Post3, 0.1,
                Post4, 0.5,
                Post5, 1.9,
                Post6, 2.2,
                Post7, 2.1,
                Post8, 1.4,
                Post9, 2.2,
                Post10,2.5,
                Post11,1.7,
                Post12,1.2,
                Post13,2.3,
                Post14,1.7,
                Post15,1.7,
                Post16,1.8,
                PostMaal],
          "S": [Post0, 1.3,
                Post0A,3,
                Post0B,0.6,
                Post1, 0.7,
                Post2, 0.9,
                Post3, 0.1,
                Post4, 0.5,
                Post5, 1.4,
                Post5A,2.3,
                Post5B,1.3,
                Post6, 2.2,
                Post7, 2.1,
                Post8, 1.4,
                Post9, 2.2,
                Post10,2.5,
                Post11,1.7,
                Post12,1.2,
                Post13,2.3,
                Post14,1.7,
                Post15,1.7,
                Post16,1.8,
                PostMaal],
          "OB": [
                Post0, 1.3,
                Post0A,3,
                Post0B,0.6,
                Post1, 0.7,
                Post2, 0.9,
                Post3, 0.1,
                Post4, 0.5,
                Post5, 1.4,
                Post5A,2.3,
                Post5B,1.3,
                Post6, 2.2,
                Post7, 2.1,
                Post8, 1.4,
                Post9, 2.2,
                Post10,2.5,
                Post11,1.7,
                Post12,1.2,
                Post13,2.3,
                Post14,1.7,
                Post15,1.7,
                Post16,1.8,
                PostMaal]}
    """ Setup course END """