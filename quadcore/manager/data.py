from quadcore.config import Config
from quadcore.manager.db import DBManager
from quadcore.models import Article, Entity

import json
import requests

class DataManager:
    db = DBManager.get_redis()

    @classmethod
    def set_article(cls, article):
        """
        Save article to database.
        """
        # Preparing auto increment
        article_count = cls.get_article_count()
        new_key = "article:" + str(article_count + 1)

        # Set key to article
        article.article_key = new_key

        # Execute HMSET for assigning hash structure
        result = cls.db.hmset(new_key, article.extract())

        # If success, increase key
        if result:
            cls.set_article_count(article_count + 1)

        return result

    @classmethod
    def set_entity(cls, entity):
        """
        Save entity to database.
        """
        # Preparing auto increment
        entity_count = cls.get_entity_count()
        new_key = "entity:" + str(entity_count + 1)

        # Set key to Entity
        entity.entity_key = new_key

        # Execute HMSET for assigning hash structure
        result = cls.db.hmset(new_key, entity.extract())

        # If success, increase key
        if result:
            cls.set_entity_count(entity_count + 1)
        return result

    @classmethod
    def update_article(cls, article):
        """
        Insert entities to article.
        """
        # Get article key from redis
        article_key = cls.db.hgetall(article.article_key)["article_key"]
        current_entity = cls.db.hget(article_key, "entities")
        update_entity = list(set(json.loads(current_entity) + article.entities))

        # Update entity list
        result = cls.db.hset(article_key, "entities", json.dumps(update_entity))

    @classmethod
    def update_entity_by_article(cls, article):
        """
        Update each entity's articles list based on article.
        """
        for entity in article.entities:
            # Get entity index from redis
            entity_index = cls.db.hget("entity_map", str(entity))
            if entity_index == None: continue

            # Generate entity key and fetch
            entity_key = "entity:" + entity_index
            given_entity = cls.get_entity_by_key(entity_index)

            # Update articles list
            if given_entity != None:
                given_entity.articles.append(article.article_key.replace("article:", ""))
                result = cls.db.hset(entity_key, "articles", json.dumps(list(set(given_entity.articles))))

    @classmethod
    def is_article_duplicate(cls, article):
        """
        Make sure new article is not duplicated.
        """
        return cls.db.hkeys("article_map").count(article.link) != 0

    @classmethod
    def get_entity_by_article(cls, article):
        """
        Choose entities based on article.
        Returns list.
        """
        # Exist check by key
        article_key = "article:" + str(article.article_key)
        article_obj = cls.db.hgetall(article_key)
        if type(article_obj) is not dict:
            return None

        # Extract
        entities = json.loads(article_obj["entities"])
        entity_list = list()
        for key in entities:
            entity_list.append(Entity.build(cls.db.get("entity:" + key)))
        return entity_list

    @classmethod
    def get_article_by_entity(cls, entities):
        """
        Choose articles based on entity.
        Returns list.
        """
        # Exist check by key
        entity_key = "entity:" + str(entity.entity_key)
        entity_obj = cls.db.hgetall(entity_key)
        if type(entity_obj) is not dict:
            return None

        # Extract
        articles = json.loads(entity_obj["articles"])
        article_list = list()
        for key in articles:
            article_list.append(Article.build(cls.db.get("article:" + key)))
        return article_list

    @classmethod
    def get_entity_by_key(cls, key):
        """
        Fetch entity by key.
        If not exist, return None.
        """
        db_key = "entity:" + str(key)
        result = cls.db.hgetall(db_key)
        return (Entity.build(result) if type(result) is dict else None)
    
    @classmethod
    def get_key_by_entity(cls, entity):
        """
        Fetch key by entity.
        If not exist, return None.
        """
        db_key = "entity:" + str(entity.entity_id)
        result = cls.db.keys(db_key)
        return (entity.entity_id if result else None)

    @classmethod
    def get_article_by_key(cls, key):
        """
        Fetch article by key.
        If not exist, return None.
        """
        db_key = "article:" + str(key)
        result = cls.db.hgetall(db_key)
        return (Article.build(result) if type(result) is dict else None)

    @classmethod
    def get_entity_count(cls):
        """
        Fetch count of entities.
        """
        return int(cls.db.get("entity_count"))

    @classmethod
    def get_article_count(cls):
        """
        Fetch count of articles.
        """
        return int(cls.db.get("article_count"))
    
    @classmethod
    def get_article_start_count(cls):
        """
        Fetch count of start article count.
        """
        return int(cls.db.get("article_start_count"))

    @classmethod
    def set_entity_count(cls, count):
        """
        Set count of entities manually.
        NOTE: this attribute should be increased automatically.
        """
        return cls.db.set("entity_count", count)
    
    @classmethod
    def set_article_count(cls, count):
        """
        Set count of articles manually.
        NOTE: this attribute should be increased automatically.
        """
        return cls.db.set("article_count", count)
    
    @classmethod
    def set_article_start_count(cls, count):
        """
        Set count of start article manually.
        """
        return cls.db.set("article_start_count", count)

    @classmethod
    def delete_article(cls, key):
        """
        Delete a certain article.
        """
        article_key = "article:" + str(key)
        hashmap = db.delete(article_key)

    @classmethod
    def delete_entity(cls, key):
        """
        Delete a certain entity.
        """
        entity_key = "entity:" + str(key)
        hashmap = db.delete(entity_key)
    
    @classmethod
    def delete_all_article(cls):
        """
        Delete all articles.
        """
        article_count = int(cls.db.get("article_count"))

        for key in range(1, article_count + 1): 
            article_key = "article:" + str(key)
            hashmap = db.delete(article_key)

    @classmethod
    def delete_all_entity(cls):
        """
        Delete all entities.
        """
        entity_count = int(cls.db.get("entity_count"))

        for key in range(1, entity_count + 1): 
            entity_key = "entity:" + str(key)
            hashmap = db.delete(entity_key)

    @classmethod
    def remain_token(cls, token, confidence=0.1, lang='en'):
        payload = {
            'token': token,
            'url': "https://arstechnica.com/?p=1251149",
            'confidence': confidence,
            'lang': lang,
        }
        remain_token = -1
        response = requests.get(Config.dandelion_url, params=payload)
        if response.status_code == 200:
            remain_token = response.headers["X-DL-units-left"] 
        
        return remain_token        

    @classmethod
    def reconnect_article(cls):
        """
        Delete article_map and create new article_map.
        """
        db = DBManager.get_redis()
        article_count = cls.get_article_count()
        
        db.delete("article_map")

        for key in range(1, article_count+1):
            article_link = cls.get_article_by_key(str(key)).link
            db.hset("article_map", article_link, "1")

    @classmethod
    def reconnect_entity(cls):
        """
        Delete entity_map and create new entity_map.
        """
        db = DBManager.get_redis()
        entity_count = cls.get_entity_count()
        
        db.delete("entity_map")

        for key in range(1, entity_count+1):
            entity = cls.get_entity_by_key(key)
            db.hset("entity_map", entity.entity_id, key)

    @classmethod
    def disconnect_article(cls):
        """
        Remove entities in article.
        """
        db = DBManager.get_redis()
        article_count = cls.get_article_count()

        for i in range(1, article_count + 1): 
            article_key = "article:" + str(i)
            hashmap = db.hset(article_key, "entities", "[]")

    @classmethod
    def disconnect_entity(cls):
        """
        Remove articles in entity.
        """
        db = DBManager.get_redis()
        entity_count = cls.get_entity_count()

        for i in range(1, entity_count + 1): 
            entity_key = "entity:" + str(i)
            hashmap = db.hset(entity_key, "articles", "[]")
