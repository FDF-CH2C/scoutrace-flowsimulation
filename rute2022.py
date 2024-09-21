"""
    Setup course - insert own course here!
    Activity: capacity, min, max, name
    """

    Post0 = Activity(8, 10, 13, "Startpost")
    Post0A = Activity(5, 10, 15, "Post 0A")
    Post0B = Activity(5, 10, 15, "Post 0B")
    Post1 = Activity(12, 25, 40, "Post 1")
    Post2 = Activity(5, 2, 5, "Post 2") # Død
    Post3 = Activity(5, 10, 15, "Post 3")
    Post4 = Activity(5, 10, 15, "Post 4")
    Post5 = Activity(5, 10, 15, "Post 5")
    Post6 = Activity(7, 15, 20, "Post 6")
    Post7 = Activity(99, 2, 5, "Post 7") # Død
    Post8 = Activity(5, 10, 15, "Post 8")
    Post9 = Activity(4, 10, 15, "Post 9") # Klatring
    Post10 = Activity(99, 60, 70, "Mad") # Opgave på madposten. Tager ikke ekstra tid
    Post11 = Activity(5, 10, 15, "Post 11")
    Post11A = Activity(99, 2, 5, "Post 11A") # Død
    Post12 = Activity(5, 10, 15, "Post 12")
    Post13 = Activity(5, 10, 15, "Post 13")
    Post14 = Activity(5, 10, 15, "Post 14")
    Post15 = Activity(30, 25, 40, "Post 15")
    Post16 = Activity(5, 10, 15, "Post 16")
    Post17 = Activity(20, 10, 60, "DFO")
    PostMaal = Activity(99, None, None, "Mål")

    Activities = [Post0, Post0A, Post0B, Post1, Post2, Post3, Post4, Post5, Post6, Post7, Post8,
                Post9, Post10, Post11, Post11A, Post12, Post13, Post14, Post15, Post16, Post17, PostMaal]

    """
    Link activities [act1, distance1, act2, distance2, ...]
    """
    course = {"V": [
                Post0, 1.9,
                Post1, 1.6,
                Post2, 0.6,
                Post3, 1.5,
                Post4, 1.2,
                Post5, 1.5,
                Post6, 1,
                Post7, 0.7,
                Post8, 0.9,
                Post9, 1.9,
                Post10, 2.1,
                Post11, 1.35,
                Post12, 1.5,
                Post13, 0,
                Post14, 1.4,
                Post15, 1.8,
                Post16, 1.2,
                Post17, 1.7,
                PostMaal],
          "S": [Post0, 1.5,
                Post0A, 1.8,
                Post0B, 1.5,
                Post1, 1.6,
                Post2, 0.6,
                Post3, 1.5,
                Post4, 1.2,
                Post5, 1.5,
                Post6, 1,
                Post7, 0.7,
                Post8, 0.9,
                Post9, 1.9,
                Post10, 2.1,
                Post11, 1.35,
                Post12, 1.5,
                Post13, 0,
                Post14, 1.4,
                Post15, 1.8,
                Post16, 1.2,
                Post17, 1.7,
                PostMaal],
          "OB": [
                Post0, 1.5,
                Post0A, 1.8,
                Post0B, 1.5,
                Post1, 1.6,
                Post2, 0.6,
                Post3, 1.5,
                Post4, 1.2,
                Post5, 1.5,
                Post6, 1,
                Post7, 0.7,
                Post8, 0.9,
                Post9, 1.9,
                Post10, 2.1,
                Post11, 1.8,
                Post11A, 1.3,
                Post12, 1.4,
                Post13, 0,
                Post14, 1.4,
                Post15, 1.8,
                Post16, 1.2,
                Post17, 1.7,
                PostMaal]}
    """ Setup course END """