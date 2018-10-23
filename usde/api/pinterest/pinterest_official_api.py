import requests
import json
from graph import Node, Edge
from graph_dict import Graph_Dict
from graph_pandas import Graph_Pandas

class PinterestOfficialAPI:
    def __init__(self, api):
        self.access_token=api["access_token"]

    def get_single_user(self, username):
        url = "https://api.pinterest.com/v1/users/" + username + "/?access_token=" + self.access_token + "&fields=first_name%2Cid%2Clast_name%2Curl%2Cimage%2Caccount_type%2Cbio%2Ccounts%2Ccreated_at"
        response = requests.request("GET", url)
        result = json.loads(response.text)
        return result

    def get_single_board(self, board_url):
        url = "https://api.pinterest.com/v1/boards/" + board_url + "/?access_token=" + self.access_token + "&fields=id%2Cname%2Curl%2Ccounts%2Ccreated_at%2Ccreator%2Cdescription%2Cimage%2Cprivacy"
        response = requests.request("GET", url)
        result = json.loads(response.text)
        return result

    def get_single_pin(self, pin_id):
        url = "https://api.pinterest.com/v1/pins/" + pin_id + "/?access_token=" + self.access_token + "&fields=note%2Curl%2Cboard%2Ccolor%2Ccounts%2Ccreated_at%2Ccreator%2Cimage%2Cid"
        response = requests.request("GET", url)
        result = json.loads(response.text)
        return result

    def get_pins_from_board(self, board_url):
        url = "https://api.pinterest.com/v1/boards/" + board_url + "/pins/?access_token=" + self.access_token + "&fields=id"
        response = requests.request("GET", url)
        result = json.loads(response.text)
        return result

    def fetch_pinterest_user_by_username(self, username):
        graph = Graph_Dict() 
        result = self.get_single_user(username)
        user = PinterestUser(result["data"])
        graph.create_node(user)
        # graph.generate_df("node")
        return graph

    def fetch_pinterest_board_by_url(self, board_url, with_pins=True, with_creator=True):
        graph = Graph_Dict() 
        board_result = self.get_single_board(board_url)
        board = PinterestBoard(board_result["data"])
        graph.create_node(board)

        creator_username = board_result["data"]["creator"]["url"].split('/')[3]
        user_result = self.get_single_user(creator_username)
        user = PinterestUser(user_result["data"])
        graph.create_node(user)

        graph.create_edge(Edge(board.get_id(), user.get_id(), "board"))
        graph.create_edge(Edge(user.get_id(), board.get_id(), "user"))

        pin_result = self.get_pins_from_board(board_url)
        for pin in pin_result["data"]:
            single_pin_result = self.get_single_pin(pin["id"])
            single_pin = PinterestPin(single_pin_result["data"])
            graph.create_node(single_pin)
            graph.create_edge(Edge(board.get_id(), single_pin.get_id(), "board"))
            graph.create_edge(Edge(single_pin.get_id(), board.get_id(), "pin"))
        
        # graph.generate_df("node")
        # graph.generate_df("edge")
        return graph

    def fetch_pinterest_pin_by_id(self, pin_id, with_board=True):
        graph = Graph()
        pin_result = self.get_single_pin(pin_id)
        pin = PinterestPin(pin_result["data"])
        graph.create_node(pin)

        creator_username = pin_result["data"]["creator"]["url"].split('/')[3]
        user_result = self.get_single_user(creator_username)
        user = PinterestUser(user_result["data"])
        graph.create_node(user)

        graph.create_edge(Edge(pin.get_id(), user.get_id(), "pin"))
        graph.create_edge(Edge(user.get_id(), pin.get_id(), "user"))

        board_url = pin_result["data"]["board"]["url"].split('/')[3] + "/" + pin_result["data"]["board"]["url"].split('/')[4]
        board_result = self.get_single_board(board_url)
        board = PinterestBoard(board_result["data"])
        graph.create_node(board)

        graph.create_edge(Edge(pin.get_id(), board.get_id(), "pin"))
        graph.create_edge(Edge(board.get_id(), pin.get_id(), "board"))
        
        # graph.generate_df("node")
        # graph.generate_df("edge")
        return graph

    def fetch_pinterest_my_usernode(self):
        url = "https://api.pinterest.com/v1/me/?access_token=" + self.access_token + "&fields=first_name%2Cid%2Clast_name%2Curl%2Cbio%2Caccount_type%2Ccounts%2Ccreated_at%2Cimage%2Cusername"
        response = requests.request("GET", url)
        result = json.loads(response.text)

        user = PinterestUser(result["data"])
        graph = Graph()
        graph.create_node(user)
        
        # graph.generate_df("node")
        return graph

    def fetch_pinterest_my_boards(self):
        graph = Graph()
        url = "https://api.pinterest.com/v1/me/?access_token=" + self.access_token + "&fields=first_name%2Cid%2Clast_name%2Curl%2Cbio%2Caccount_type%2Ccounts%2Ccreated_at%2Cimage%2Cusername"
        response = requests.request("GET", url)
        result = json.loads(response.text)
        user = PinterestUser(result["data"])
        graph.create_node(user)

        url = "https://api.pinterest.com/v1/me/boards/?access_token=" + self.access_token + "&fields=id%2Cname%2Curl%2Ccounts%2Ccreated_at%2Ccreator%2Cdescription%2Cimage%2Cprivacy"
        response = requests.request("GET", url)
        result = json.loads(response.text)

        for myboard in result["data"]:
            board = PinterestBoard(myboard)
            graph.create_node(board)
            graph.create_edge(Edge(board.get_id(), user.get_id(), "board"))
            graph.create_edge(Edge(user.get_id(), board.get_id(), "user"))

        # graph.generate_df("node")
        # graph.generate_df("edge")
        return graph

    def fetch_pinterest_my_pins(self):
        graph = Graph()
        url = "https://api.pinterest.com/v1/me/?access_token=" + self.access_token + "&fields=first_name%2Cid%2Clast_name%2Curl%2Cbio%2Caccount_type%2Ccounts%2Ccreated_at%2Cimage%2Cusername"
        response = requests.request("GET", url)
        result = json.loads(response.text)
        user = PinterestUser(result["data"])
        graph.create_node(user)

        url = "https://api.pinterest.com/v1/me/pins/?access_token=" + self.access_token + "&fields=note%2Curl%2Cboard%2Ccolor%2Ccounts%2Ccreated_at%2Ccreator%2Cimage%2Cid"
        response = requests.request("GET", url)
        result = json.loads(response.text)

        for mypin in result["data"]:
            pin = PinterestPin(mypin)
            graph.create_node(pin)
            graph.create_edge(Edge(pin.get_id(), user.get_id(), "pin"))
            graph.create_edge(Edge(user.get_id(), pin.get_id(), "user"))

        graph.generate_df("node")
        graph.generate_df("edge")
        return graph


    def fetch_pinterest_my_followers(self):
        graph = Graph()
        url = "https://api.pinterest.com/v1/me/?access_token=" + self.access_token + "&fields=first_name%2Cid%2Clast_name%2Curl%2Cbio%2Caccount_type%2Ccounts%2Ccreated_at%2Cimage%2Cusername"
        response = requests.request("GET", url)
        result = json.loads(response.text)
        user = PinterestUser(result["data"])
        graph.create_node(user)

        url = "https://api.pinterest.com/v1/me/followers/?access_token=" + self.access_token + "&fields=first_name%2Cid%2Clast_name%2Curl%2Cbio%2Caccount_type%2Ccounts%2Ccreated_at%2Cimage%2Cusername"
        response = requests.request("GET", url)
        result = json.loads(response.text)

        for myfollower in result["data"]:
            follower = PinterestUser(myfollower)
            graph.create_node(follower)
            graph.create_edge(Edge(user.get_id(), follower.get_id(), "user"))
        
        graph.generate_df("node")
        graph.generate_df("edge")
        return graph

    def fetch_pinterest_my_following_users(self):
        graph = Graph()
        url = "https://api.pinterest.com/v1/me/?access_token=" + self.access_token + "&fields=first_name%2Cid%2Clast_name%2Curl%2Cbio%2Caccount_type%2Ccounts%2Ccreated_at%2Cimage%2Cusername"
        response = requests.request("GET", url)
        result = json.loads(response.text)
        user = PinterestUser(result["data"])
        graph.create_node(user)

        url = "https://api.pinterest.com/v1/me/following/users/?access_token=" + self.access_token + "&fields=first_name%2Cid%2Clast_name%2Curl%2Cbio%2Caccount_type%2Ccounts%2Ccreated_at%2Cimage%2Cusername"
        response = requests.request("GET", url)
        result = json.loads(response.text)

        for myfollowing in result["data"]:
            following = PinterestUser(myfollowing)
            graph.create_node(following)
            graph.create_edge(Edge(user.get_id(), following.get_id(), "user"))
        
        graph.generate_df("node")
        graph.generate_df("edge")
        return graph

    def fetch_pinterest_my_following_boards(self):
        graph = Graph()
        url = "https://api.pinterest.com/v1/me/?access_token=" + self.access_token + "&fields=first_name%2Cid%2Clast_name%2Curl%2Cbio%2Caccount_type%2Ccounts%2Ccreated_at%2Cimage%2Cusername"
        response = requests.request("GET", url)
        result = json.loads(response.text)
        user = PinterestUser(result["data"])
        graph.create_node(user)

        url = "https://api.pinterest.com/v1/me/following/boards/?access_token=" + self.access_token + "&fields=id%2Cname%2Curl%2Ccounts%2Ccreated_at%2Ccreator%2Cdescription%2Cimage%2Cprivacy"
        response = requests.request("GET", url)
        result = json.loads(response.text)

        for myfollowingboard in result["data"]:
            followingboard = PinterestBoard(myfollowingboard)
            graph.create_node(followingboard)
            graph.create_edge(Edge(user.get_id(), followingboard.get_id(), "user"))
            
            creator_username = myfollowingboard["creator"]["url"].split('/')[3]
            creator_result = self.get_single_user(creator_username)
            creator = PinterestUser(creator_result["data"])
            graph.create_node(creator)

            graph.create_edge(Edge(followingboard.get_id(), creator.get_id(), "board"))
            graph.create_edge(Edge(creator.get_id(), followingboard.get_id(), "user"))

            board_url = myfollowingboard["url"].split('/')[3] + "/" + myfollowingboard["url"].split('/')[4]
            pin_result = self.get_pins_from_board(board_url)
            for pin in pin_result["data"]:
                single_pin_result = self.get_single_pin(pin["id"])
                single_pin = PinterestPin(single_pin_result["data"])
                graph.create_node(single_pin)
                graph.create_edge(Edge(followingboard.get_id(), single_pin.get_id(), "board"))
                graph.create_edge(Edge(single_pin.get_id(), followingboard.get_id(), "pin"))
        
        graph.generate_df("node")
        graph.generate_df("edge")
        return graph


class PinterestUser(Node):
    def __init__(self, result):
        label = result["first_name"] + " " + result["last_name"]
        # Node.__init__(self, id, label, label_attribute)
        Node.__init__(self, result["id"], label, "user")
        self.bio = result["bio"]
        self.first_name = result["first_name"]
        self.last_name = result["last_name"]
        self.account_type = result["account_type"]
        self.url = result["url"]
        self.image_url = result["image"]["60x60"]["url"]
        self.created_at = result["created_at"]
        self.pins_count = result["counts"]["pins"]
        self.following_count = result["counts"]["following"]
        self.followers_count = result["counts"]["followers"]
        self.boards_count = result["counts"]["boards"]

class PinterestBoard(Node):
    def __init__(self, result): 
        Node.__init__(self, result["id"], result["name"], "board")
        self.url = result["url"]
        self.image_url = result["image"]["60x60"]["url"]
        self.created_at = result["created_at"]
        self.privacy = result["privacy"]
        self.pins_count = result["counts"]["pins"]
        self.collaborators_count = result["counts"]["collaborators"]
        self.followers_count = result["counts"]["followers"]
        self.description = result["description"]

class PinterestPin(Node):
    def __init__(self, result):
        Node.__init__(self, result["id"], "pin_" + result["id"], "pin")         
        self.url = result["url"]
        self.image_url = result["image"]["original"]["url"]
        self.created_at = result["created_at"]
        self.note = result["note"]
        self.color = result["color"]
        self.saves = result["counts"]["saves"]
        self.comments = result["counts"]["comments"]
