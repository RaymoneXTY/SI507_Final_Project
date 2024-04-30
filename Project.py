import json
import pandas as pd
from igdb.wrapper import IGDBWrapper
from requests import post
import os
import json
from DataStructure import Game, GameGraph

# IGDB API credentials
client_id = 'YOUR_CLIENT_ID' # Your client ID
client_secret = 'YOUR_CLIENT_SECRET' # Your client secret
token = 'YOUR_ACCESS_TOKEN' # Your access token
wrapper = IGDBWrapper(client_id, token) # Create a new instance of the IGDBWrapper


def fetch_game_data():
    '''Create a list of dictionaries containing the top 5000 games from the IGDB database. If the file already exists, read the cache file.'''
    if os.path.exists('data/top_5000_games.csv'):
        top_5000_games = pd.read_csv('data/top_5000_games.csv').to_dict('records')
    else:
        '''use the IGDB wrapper'''
        # JSON API request
        byte_array = wrapper.api_request(
                    'games',
                    'fields id, name;'
                )
        games = []
        # Protobuf API request
        from igdb.igdbapi_pb2 import GameResult
        byte_array = wrapper.api_request(
                    'games.pb',
                    'fields name, platforms, involved_companies, genres, themes, keywords; limit 500; sort total_rating desc; where total_rating_count > 10 & category = 0;' #category 0 is main game (not dlc, expansion, etc.)
                )
        games_message = GameResult()
        games_message.ParseFromString(byte_array) # Fills the protobuf message object with the response
        games.extend(games_message.games) # games is a list of Game objects

        offset = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500]
        # get the next 4500 games
        for i in offset:
            byte_array = wrapper.api_request(
                    'games.pb',
                '   fields name, platforms, involved_companies, genres, themes, keywords; limit 500; sort total_rating desc; where total_rating_count > 10 & category = 0; offset ' + str(i) + ';'
                )
            games_message = GameResult()
            games_message.ParseFromString(byte_array) 
            games.extend(games_message.games) 

        # convert the list of games to a list of dictionaries
        top_5000_games = []
        for game in games:
            game_dict = {
                'id': game.id,
                'name': game.name,
                'platforms': game.platforms,
                'involved_companies': game.involved_companies,
                'genres': game.genres,
                'themes': game.themes,
                'keywords': game.keywords
            }
            top_5000_games.append(game_dict)

        # convert the platforms, involved_companies, genres, themes, and keywords to a list of numbers
        for game in top_5000_games:
            if game['platforms']:
                game['platforms'] = f"{[platform.id for platform in game['platforms']]}"
            if game['involved_companies']:
                game['involved_companies'] = f"{[company.id for company in game['involved_companies']]}"
            if game['genres']:
                game['genres'] = f"{[genre.id for genre in game['genres']]}"
            if game['themes']:
                game['themes'] = f"{[theme.id for theme in game['themes']]}"
            if game['keywords']:
                game['keywords'] = f"{[keyword.id for keyword in game['keywords']]}"

        # save to a csv file
        df = pd.DataFrame(top_5000_games)
        df.to_csv('data/top_5000_games.csv', index=False)
    return top_5000_games

def fetch_platform_data():
    '''Create a csv file containing the platforms from the IGDB database. If the file already exists, read the cache file.'''
    if os.path.exists('data/platforms.csv'):
        platforms = pd.read_csv('data/platforms.csv').to_dict('records')
    else:
        # get the platform names
        token_B = f'Bearer {token}'
        response = post('https://api.igdb.com/v4/platforms', **{'headers': {'Client-ID': client_id, 'Authorization': token_B},'data': 'fields name; sort created_at asc; limit 300;'})
        # There are 210 platforms in the IGDB database
        platforms = response.json()
        # save the list of dictionaries to a csv file
        df = pd.DataFrame(platforms)
        df.to_csv('data/platforms.csv', index=False)
    return platforms

def fetch_genre_data():
    '''Create a csv file containing the genres from the IGDB database. If the file already exists, read the cache file.'''
    if os.path.exists('data/genres.csv'):
        genres = pd.read_csv('data/genres.csv').to_dict('records')
    else:
        # get the genre names
        token_B = f'Bearer {token}'
        response = post('https://api.igdb.com/v4/genres', **{'headers': {'Client-ID': client_id, 'Authorization': token_B},'data': 'fields name; sort created_at asc; limit 50;'})
        # There are 23 genres in the IGDB database
        genres = response.json()
        # save the list of dictionaries to a csv file
        df = pd.DataFrame(genres)
        df.to_csv('data/genres.csv', index=False)
    return genres

def fetch_theme_data():
    '''Create a csv file containing the themes from the IGDB database. If the file already exists, read the cache file.'''
    if os.path.exists('data/themes.csv'):
        themes = pd.read_csv('data/themes.csv').to_dict('records')
    else:
        # get the theme names
        token_B = f'Bearer {token}'
        response = post('https://api.igdb.com/v4/themes', **{'headers': {'Client-ID': client_id, 'Authorization': token_B},'data': 'fields name; sort created_at asc; limit 50;'})
        # There are 22 themes in the IGDB database
        themes = response.json()
        # save the list of dictionaries to a csv file
        df = pd.DataFrame(themes)
        df.to_csv('data/themes.csv', index=False)
    return themes

def load_network(game_data):
    '''Load an existing game network from JSON and recreate the Game objects and their connections.'''
    file_path = 'data/game_network.json'
    if not os.path.exists(file_path):
        print("Network file does not exist.")
        return None

    with open(file_path, 'r') as file:
        network_json = json.load(file)

    graph = GameGraph()
    id_to_game = {}

    # Recreate all Game objects and ensure the game IDs are strings
    for game_info in game_data:
        game_id_str = str(game_info['id'])  # Convert to string to match JSON keys
        game = Game(game_id_str, game_info['name'], game_info['platforms'],
                    game_info['involved_companies'], game_info['genres'], game_info['themes'], game_info['keywords'])
        graph.add_game(game)
        id_to_game[game_id_str] = game

    # Reestablish the neighbor relationships with exact connection points
    for game_id_str, neighbors_info in network_json.items():
        game = id_to_game.get(game_id_str)
        if game:
            for neighbor_info in neighbors_info:
                neighbor_id_str, connection_points = map(str, neighbor_info)  # Convert to string to match JSON keys
                neighbor_game = id_to_game.get(neighbor_id_str)
                if neighbor_game:
                    game.add_neighbor(neighbor_game, connection_points)
                else:
                    print(f"Neighbor game with ID {neighbor_id_str} not found.")
        else:
            print(f"Game with ID {game_id_str} not found in game_data.")

    return graph


def create_game_network(game_data):
    '''Create a game network based on the top 5000 games. If the network cache exists, load it.'''
    file_path = 'game_network.json'
    if os.path.exists(file_path):
        print("Loading cached network.")
        network = load_network(game_data)  # Ensure game_data is passed to recreate the objects
    else:
        print("Creating new network...")
        graph = GameGraph()
        # Ensure that game IDs are converted to strings, as they will be keys in the JSON object
        for game in game_data:
            game_id_str = str(game['id'])
            new_game = Game(game_id_str, game['name'], game['platforms'], game['involved_companies'], 
                            game['genres'], game['themes'], game['keywords'])
            graph.add_game(new_game)

        graph.build_network()
        graph.get_top_neighbors()

        # Serialize the network with game IDs as strings and their connection points
        network_info = {game.game_id: [[neighbor.game_id, points] for neighbor, points in game.neighbors.items()]
                        for game in graph.games.values()}
        # Save the JSON to a file
        with open(file_path, 'w') as file:
            json.dump(network_info, file, indent=4)

        network = graph

    return network



def get_game_information(game_data, platform_data, genre_data, theme_data, message=None):
    """implement a function to accept a game id or game name and return the game's name, platform, genre and theme"""
    if message:
        pass
    else:
        message = input("Enter a game id or name to get information: ")
    if str(message).isdigit():
        for game in game_data:
            if game['id'] == int(message):
                game_name = game['name']
                game_id = game['id']
                platform_ids = game['platforms']
                genre_ids = game['genres']
                theme_ids = game['themes']
                break
        else:
            return "Game not found, please enter another game id or name."
    else:
        for game in game_data:
            if game['name'].lower().strip() == message.lower().strip():
                game_name = game['name']
                game_id = game['id']
                platform_ids = game['platforms']
                genre_ids = game['genres']
                theme_ids = game['themes']
                break
        else:
            return "Game not found, please enter another game id or name."
    platform_names = []
    for platform in platform_data:
        if str(platform['id']) in platform_ids:
            platform_names.append(platform['name'])
    genre_names = []
    for genre in genre_data:
        if str(genre['id']) in genre_ids:
            genre_names.append(genre['name'])
    theme_names = []
    for theme in theme_data:
        if str(theme['id']) in theme_ids:
            theme_names.append(theme['name'])
    return {'game name': game_name, 'platforms': platform_names, 'genres': genre_names, 'themes': theme_names}

def get_game_recommendations(game_data, network_data):
    """implement a function to accept a game id or name and return neighbors of the game in the game network"""
    message = input("Enter your favorite game's id or name to get recommended games: ")
    if message.isdigit():
        for game in game_data:
            if game['id'] == int(message):
                name = game['name']
                game_id = game['id']
                break
        else:
            return "Game not found, please enter another game id or name."
    else:
        for game in game_data:
            if game['name'].lower().strip() == message.lower().strip():
                game_id = game['id']
                break
        else:
            return "Game not found, please enter another game id or name."

    game = network_data.games.get(str(game_id))
    if game:
        neighbors = [(neighbor.game_id, points) for neighbor, points in game.neighbors.items()]
        recommended_ids = [neighbor[0] for neighbor in neighbors]
        recommended_games = {1: "", 2: "", 3: "", 4: "", 5: "", 6: "", 7: "", 8: "", 9: "", 10: ""}
        # keep the original order of the games with their names
        for i in range(1, 11):
            for game in game_data:
                if str(game['id']) in recommended_ids:
                    recommended_games[i] = game['name']
                    recommended_ids.remove(str(game['id']))
                    break
        return recommended_games

    else:
        return "Game not found, please enter another game id or name."




def main():
    print("Welcome to the Game Network Explorer! I collected the top rated 5000 games from the IGDB database. You can search for a game and get detailed information or get 10 recommended games based on the game network. Have fun exploring!")
    print("Loading data...")
    top_5000_games = fetch_game_data()
    platforms = fetch_platform_data()
    genres = fetch_genre_data()
    themes = fetch_theme_data()
    print("Data loaded successfully!")
    network = load_network(top_5000_games)
    if not network:
        network = create_game_network(top_5000_games)
    print("Game Network prepared!")
    while True:
        print("\nOptions:")
        print("1. Get detailed information of a game")
        print("2. Get recommended games")
        print("Press 'q' to quit")
        choice = input("Please choose an option (1, 2, q): ")

        if choice.lower() == 'q':
            print("Exiting program. Thank you for using the Game Network Explorer!")
            break
        
        if choice == '1':
            game_info = get_game_information(top_5000_games, platforms, genres, themes)
            print(game_info)
        elif choice == '2':
            recommendations = get_game_recommendations(top_5000_games, network)
            print("Recommended Games:", recommendations)
            if recommendations != "Game not found, please enter another game id or name.":
                detailed_info_choice = input("Do you want to get detailed information on one of these recommended games? (yes/no): ")
                if detailed_info_choice.lower() == 'yes':
                    game_num = input("Input the ranking number of the recommended game(1-10) you want to get more information: ")
                    game_name = recommendations[int(game_num)]
                    for game in top_5000_games:
                        if game['name'] == game_name:
                            game_id = game['id']
                            print(get_game_information(top_5000_games, platforms, genres, themes, message=game_id))
                            break
        else:
            print("Invalid option. Please choose a valid option.")

        continue_choice = input("\nDo you want to continue using the Game Network Explorer? (yes/no): ")
        if continue_choice.lower() != 'yes':
            print("Exiting program. Thank you for using the Game Network Explorer!")
            break


if __name__ == '__main__':
    main()
