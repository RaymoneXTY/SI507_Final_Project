
from igdb.wrapper import IGDBWrapper

client_id = 'evqlup6s15iw9nqlt1fag38k6yshan'
client_secret = 'tkmzjahxnhop25aw76v0mxm2tukbp2'

wrapper = IGDBWrapper(client_id, '97ibqjqietx7ecz9wc3e4hu50kplwv')


'''With a wrapper instance already created'''
# JSON API request
byte_array = wrapper.api_request(
            'games',
            'fields id, name;'
          )
# parse into JSON however you like...

# Protobuf API request
from igdb.igdbapi_pb2 import GameResult
byte_array = wrapper.api_request(
            'games.pb', # Note the '.pb' suffix at the endpoint
            'fields name, genres; limit 50; sort popularity desc; where rating > 90;'
          )
games_message = GameResult()
games_message.ParseFromString(byte_array) # Fills the protobuf message object with the response
games = games_message.games

print(games)