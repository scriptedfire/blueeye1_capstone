substation_data = {1 : {"lat" : 33.613499, "long" : -87.373673, "ground_r" : 0.2},
                   2 : {"lat" : 34.310437, "long" : -86.365765, "ground_r" : 0.2},
                   3 : {"lat" : 33.955058, "long" : -84.679354, "ground_r" : 0.2},}

bus_data = {1 : {"sub_num" : 1}, 2 : {"sub_num" : 1},
            3 : {"sub_num" : 2}, 4 : {"sub_num" : 2},
            5 : {"sub_num" : 3}, 6 : {"sub_num" : 3}}

branch_data = {(2, 3, 1) : {"has_trans" : False, "resistance" : 3.525,
                            "type" : None, "trans_w1" : None, "trans_w2" : None},
                (4, 5, 1) : {"has_trans" : False, "resistance" : 4.665,
                                "type" : None, "trans_w1" : None, "trans_w2" : None},
                (1, 2, 1) : {"has_trans" : True, "resistance" : None,
                                "type" : "gsu", "trans_w1" : 0.5, "trans_w2" : None},
                (3, 4, 1) : {"has_trans" : True, "resistance" : None,
                            "type" : "auto", "trans_w1" : 0.2, "trans_w2" : 0.2},
                (5, 6, 1) : {"has_trans" : True, "resistance" : None,
                            "type" : "gsu", "trans_w1" : 0.5, "trans_w2" : None}}
