from py2neo import Graph, Node, Relationship, authenticate
from passlib.hash import bcrypt
from datetime import datetime
import os
import uuid

url = os.environ.get('GRAPHENEDB_URL', 'http://localhost:7474')
username = "neo4j"
password = "weibo-project"

if username and password:
    authenticate(url.strip('http://'), username, password)

graph = Graph(url + '/db/data/')


class User:

    def __init__(self, user_id):
        self.user_id = user_id


    @classmethod
    def find_by_email(cls, user_email):
        user = graph.find_one("User", "email", user_email)
        return user

    @classmethod
    def find_by_id(cls, user_id):
        user = graph.find_one("User", "id", user_id)
        return user

    @classmethod
    def register(cls, email, password, nickname):
        if not User.find_by_email(email):
            user = Node("User", id=str(uuid.uuid4()), email=email, password=bcrypt.encrypt(password), nickname=nickname)
            graph.create(user)
            return True
        else:
            return False
    
    @classmethod
    def verify_password(cls, email, password):
        user = User.find_by_email(email)
        if user:
            return bcrypt.verify(password, user['password'])
        else:
            return False

    @classmethod
    def add_post(cls, user_id, content, tags):
        user = User.find_by_id(user_id)
        post = Node(
            "Post",
            id=str(uuid.uuid4()), 
            content=content,
            timestamp=timestamp(),
            date=date()
        )
        rel = Relationship(user, "PUBLISHED", post)
        graph.create(rel)

    @classmethod
    def like_post(cls, user_id, post_id):
        user = User.find_by_id(user_id)
        post = graph.find_one("Post", "id", post_id)
        graph.create_unique(Relationship(user, "LIKED", post))

    @classmethod
    def follow_user(cls, fans_id, target_id):
        fans = User.find_by_id(fans_id)
        target = User.find_by_id(target_id)
        graph.create_unique(Relationship(fans, "FOLLOWED", target))

    @classmethod
    def is_following(cls, fans_id, target_id):
        query = 'MATCH (:User {id:{fans_id}})-[r:FOLLOWED]->(:User {id:{target_id}}) RETURN r LIMIT 1'
        r = graph.cypher.execute(query, fans_id=fans_id, target_id=target_id)
        return r.one != None
  
    @classmethod
    def retrieve_posts(cls, user_id):
        query = 'MATCH (u:User {id:{user_id}})-[:PUBLISHED]->(p:Post) RETURN u,p LIMIT 25'
        return graph.cypher.execute(query, user_id=user_id)

    @classmethod
    def retrieve_feed(cls, user_id):
        # TODO: Should order by time desc
        query = 'MATCH (:User {id:{user_id}})-[:FOLLOWED]->(u:User)-[:PUBLISHED]->(p:Post) RETURN u,p LIMIT 25'
        return graph.cypher.execute(query, user_id=user_id)


def timestamp():
    epoch = datetime.utcfromtimestamp(0)
    now = datetime.now()
    delta = now - epoch
    return delta.total_seconds()

def date():
    return datetime.now().strftime('%F')




