from gensim.models.word2vec import Word2Vec
import spacy
import pickle
import emoji
import MeCab
import numpy as np
import scipy
import random
import os
import re
from google.cloud import storage

class Emojize:
    def __init__(self):
        self.storage_client = storage.Client()
        self.model = self.read_pickle_from_gcs(os.getenv('MODEL_PATH'))
        self.emoji_vector_dic = self.read_pickle_from_gcs(os.getenv('EMOJI_VECTOR_DIC_PATH'))
        self.emoji_vectors = list(self.emoji_vector_dic.values())
        self.emojis = list(self.emoji_vector_dic.keys())
        self.nlp = spacy.load('ja_ginza')
        self.mecab = MeCab.Tagger()
        self.WORD_TYPES = ['名詞', '形容詞', '動詞']
        self.SUB_TYPES = ["数", "非自立", "代名詞", "接尾"]
        self.EMOJI_N = int(os.getenv('EMOJI_N'))
        self.CLOSEST_N = int(os.getenv('CLOSEST_N'))
        self.BUNMATSU_DIC = {'!': '❗️', '！':'❗️', '!!':'‼️', '‼︎':'‼️', '?': '❓', '？': '❓', '⁉︎': '⁉️'}

    def __call__(self, tweet, emoji_level=3):
        self.EMOJI_LEVEL=emoji_level
        return self.emojize_tweet(tweet)

    def emojize_tweet(self, tweet):
        res_tweet = ''
        tweets = re.split('[\n\s\t]', tweet)
        for tweet in tweets:
            doc = self.nlp(tweet)
            
            for text in doc.sents:
                tweet_emojized = self.emojize(str(text))
                res_tweet += tweet_emojized if res_tweet == '' else '\n' + tweet_emojized

        return res_tweet

    def emojize(self, text):
        text = text.replace('。', '')
        node = self.mecab.parseToNode(text)
        res_text = ''
        bunmatsu_emoji_word = None
        
        while node:
            if node.surface != "":
                wordtype = node.feature.split(",")[0]
                subtype = node.feature.split(",")[1]
                # print({node.surface: subtype})
                original = node.feature.split(",")[6]
                next_node = node.next

                if (wordtype in self.WORD_TYPES and subtype not in self.SUB_TYPES and original != '*' and original in self.model.wv):
                    bunmatsu_emoji_word = original
                
                # 文末のときの絵文字選ぶ
                if next_node.surface == "":
                    # 文末が!や?だったらそれを絵文字にカウントする
                    if node.surface in self.BUNMATSU_DIC:
                        res_text += self.BUNMATSU_DIC[node.surface]
                        
                        if self.EMOJI_LEVEL != 1:
                            cosine_similarity_results_ids = self.get_cosine_similarity_results_ids(bunmatsu_emoji_word)
                            res_text += self.select_emoji(cosine_similarity_results_ids)
                    else:
                        cosine_similarity_results_ids = self.get_cosine_similarity_results_ids(bunmatsu_emoji_word)
                        res_text += node.surface
                        if self.EMOJI_LEVEL == 1:
                            res_text += self.select_emoji(cosine_similarity_results_ids)
                        else:
                            res_text += self.select_emoji(cosine_similarity_results_ids, emoji_n_count=2) 
                        
                # 絵文字レベルが3のときの文中の絵文字を選ぶ
                elif bunmatsu_emoji_word == original and\
                    self.EMOJI_LEVEL == 3 and wordtype == '名詞' and subtype == '一般':
                    cosine_similarity_results_ids = self.get_cosine_similarity_results_ids(original)
                    res_text += node.surface + self.select_emoji(cosine_similarity_results_ids)
                else:
                    res_text += node.surface

            node = node.next
            if node is None:
                break

        return res_text

    def select_emoji(self, results_ids, emoji_n_count=1):
        emojis_selected = [self.emojis[index] for index in random.sample(results_ids[:self.CLOSEST_N], emoji_n_count)]
        return ''.join(emojis_selected)

    def get_cosine_similarity_results_ids(self, word):
        text_vector = self.model.wv[word]
        distances = scipy.spatial.distance.cdist([text_vector], self.emoji_vectors, metric="cosine")[0]
        results = zip(range(len(distances)), distances)
        results = sorted(results, key=lambda x: x[1])
        results_ids = [result[0] for result in results]

        return results_ids

    def test(self, keyword):
        text_vector = self.model.wv[keyword]
        distances = scipy.spatial.distance.cdist([text_vector], self.emoji_vectors, metric="cosine")[0]
        results = zip(range(len(distances)), distances)
        results = sorted(results, key=lambda x: x[1])
        for res in results[:10]:  
            print(self.emojis[res[0]])
            
    def read_pickle_from_gcs(self, path):
        bucket = self.storage_client.bucket(os.getenv('GCS_BUCKET_NAME'))
        blob = bucket.blob(path)
        pickle_in = blob.download_as_string()
        file_loaded = pickle.loads(pickle_in)

        return file_loaded