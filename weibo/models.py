# -*- coding: utf-8 -*-

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
    def unlike_post(cls, user_id, post_id):
        query = 'MATCH (:User {id:{user_id}})-[r:LIKED]->(:Post {id:{post_id}}) RETURN r'
        rel = graph.cypher.execute(query, user_id=user_id, post_id=post_id).one
        if rel:
            rel.delete()
            return True
        return False

    @classmethod
    def follow_user(cls, fans_id, target_id):
        fans = User.find_by_id(fans_id)
        target = User.find_by_id(target_id)
        graph.create_unique(Relationship(fans, "FOLLOWED", target))

    @classmethod
    def unfollow_user(cls, fans_id, target_id):
        query = 'MATCH (:User {id:{fans_id}})-[r:FOLLOWED]->(:User {id:{target_id}}) RETURN r'
        rel = graph.cypher.execute(query, fans_id=fans_id, target_id=target_id).one
        if rel:
            rel.delete()
        
    @classmethod
    def is_following(cls, fans_id, target_id):
        query = 'MATCH (:User {id:{fans_id}})-[r:FOLLOWED]->(:User {id:{target_id}}) RETURN r LIMIT 1'
        r = graph.cypher.execute(query, fans_id=fans_id, target_id=target_id)
        return r.one != None
  
    @classmethod
    def retrieve_posts(cls, user_id):
        query = """
        MATCH (u:User {id: {user_id}})-[:PUBLISHED]->(p:Post)
        OPTIONAL MATCH  (u:User {id:{user_id}})-[:PUBLISHED]->(p:Post)<-[:COMMENTED]-(c:Comment)
        OPTIONAL MATCH ()-[r:LIKED]->(p:Post)
        OPTIONAL MATCH (:User {id: {user_id}})-[me:LIKED]->(p:Post)
        RETURN u,p,COUNT(r) AS total_like, COUNT(me) AS my_like, COUNT(c) AS c
        ORDER BY p.timestamp DESC LIMIT 25
        """
        return graph.cypher.execute(query, user_id=user_id)

    @classmethod
    def retrieve_feed(cls, user_id):
        query = """
        MATCH (:User {id:{user_id}})-[:FOLLOWED]->(u:User)-[:PUBLISHED]->(p:Post)
        OPTIONAL MATCH()-[c:COMMENTED]->(p:Post)
        OPTIONAL MATCH ()-[r:LIKED]->(p:Post)
        OPTIONAL MATCH (:User {id: {user_id}})-[me:LIKED]->(p:Post)
        RETURN u,p,COUNT(r) AS total_like, COUNT(me) AS my_like, COUNT(c) AS c
        ORDER BY p.timestamp DESC LIMIT 25"""
        return graph.cypher.execute(query, user_id=user_id)

    @classmethod
    def add_comment_on_post(cls, user_id, user_id_of_target, post_id, content, tags):
        user = User.find_by_id(user_id)
        comment = Node(
            "Comment",
            id=str(uuid.uuid4()),
            content=content,
            timestamp=timestamp(),
            date=date()
        )
        rel_publish = Relationship(user, "PUBLISHED", comment)
        graph.create(rel_publish)
        Comment.comment_on_post(comment["id"], user_id_of_target, post_id, tags)

    @classmethod
    def add_comment_on_comment(cls, user_id, user_id_of_target, post_id, content, tags):
        user = User.find_by_id(user_id)
        comment = Node(
            "Comment",
            id=str(uuid.uuid4()),
            content=content,
            timestamp=timestamp(),
            date=date()
        )
        target_user = User.find_by_id(user_id_of_target)
        rel_publish = Relationship(user, "PUBLISHED", comment)
        graph.create(rel_publish)
        Comment.comment_on_comment(comment["id"], user_id_of_target, post_id, tags)

    @classmethod
    def like_comment(cls, user_id, comment_id):
        user = User.find_by_id(user_id)
        comment = graph.find_one("Comment", "id", comment_id)
        graph.create_unique(Relationship(user, "LIKED", comment))

class Post:
    @classmethod
    def find_by_id(cls, post_id):
        post = graph.find_one("Post", "id", post_id)
        return post

    @classmethod
    def retrieve_comments(cls, post_id):
        query = 'MATCH (u:User)-[:PUBLISHED]->(c:Comment)-[:COMMENTED]->(Post{id:{post_id}})\
				 OPTIONAL MATCH (u:User)-[:PUBLISHED]->(c:Comment)-[:REPLIED]-> (t:User) \
				 RETURN u,c,t ORDER BY c.timestamp DESC LIMIT 25'
        return graph.cypher.execute(query, post_id=post_id)
    
    @classmethod
    def count_like(cls, post_id):
        query = 'MATCH ()-[r:LIKED]->(:Post {id:{post_id}}) RETURN COUNT(r)'
        return graph.cypher.execute(query, post_id=post_id).one

    @classmethod
    def retrieve_likes(cls, post_id):
        query = 'MATCH (u:User)-[:LIKED]->(Post{id:{post_id}}) RETURN u ORDER BY u.nickname ASC LIMIT 25'
        return graph.cypher.execute(query, post_id=post_id)

    @classmethod
    def find_poster(cls, post_id):
        query = 'MATCH (u:User)-[:PUBLISHED]->(Post{id:{post_id}}) RETURN u ORDER BY u.nickname ASC LIMIT 1'
        return graph.cypher.execute(query, post_id=post_id)
		
class Comment:
    @classmethod
    def find_by_id(cls, comment_id):
        comment = graph.find_one("Comment", "id", comment_id)
        return comment

    @classmethod
    def comment_on_post(cls, comment_id, post_user_id, post_id, tags):
        comment = Comment.find_by_id(comment_id)
        post_user = Post.find_by_id(post_id)
        post = Post.find_by_id(post_id)
        rel_comment_on_post = Relationship(comment, "REPLIED", post_user)
        graph.create(rel_comment_on_post)
        rel_comment_on_post = Relationship(comment, "COMMENTED", post)
        graph.create(rel_comment_on_post)

    @classmethod
    def comment_on_comment(cls, comment_id, post_user_id, post_id, tags):
        comment = Comment.find_by_id(comment_id)
        post_user = User.find_by_id(post_user_id)
        post = Post.find_by_id(post_id)
        rel_reply = Relationship(comment, "REPLIED", post_user)
        graph.create(rel_reply)
        rel_comment_on_post = Relationship(comment, "COMMENTED", post)
        graph.create(rel_comment_on_post)


def get_recent_posts(user_id = None):
    if user_id:
        query = """
        MATCH (u:User)-[:PUBLISHED]->(p:Post)
        OPTIONAL MATCH ()-[r:LIKED]->(p:Post)
        OPTIONAL MATCH (:User {id: {user_id}})-[me:LIKED]->(p:Post)
        OPTIONAL MATCH  (u:User)-[:PUBLISHED]->(p:Post)<-[:COMMENTED]-(c:Comment)
        RETURN u,p,COUNT(r) AS total_like, COUNT(me) AS my_like, COUNT(c) AS c
        ORDER BY p.timestamp DESC LIMIT 25
        """
        return graph.cypher.execute(query, user_id=user_id)
    else:
        query = """
        MATCH (u:User)-[:PUBLISHED]->(p:Post)
        OPTIONAL MATCH ()-[r:LIKED]->(p:Post)
        OPTIONAL MATCH  (u:User)-[:PUBLISHED]->(p:Post)<-[:COMMENTED]-(c:Comment)
        RETURN u,p,COUNT(r) AS total_like, COUNT(c) AS c
        ORDER BY p.timestamp DESC LIMIT 25
        """
        return graph.cypher.execute(query)


def timestamp():
    epoch = datetime.utcfromtimestamp(0)
    now = datetime.now()
    delta = now - epoch
    return delta.total_seconds()

def date():
    return datetime.now().strftime('%Y-%m-%d')




