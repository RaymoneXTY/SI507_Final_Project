class Game:
    '''Game class to store the game information and its neighbors in the network.'''
    def __init__(self, game_id, name, platforms, companies, genres, themes, keywords):
        self.game_id = game_id
        self.name = name
        self.platforms = platforms
        self.companies = companies
        self.genres = genres
        self.themes = themes
        self.keywords = keywords
        self.neighbors = {}  # This will store the neighboring games and their connection points

    def add_neighbor(self, other_game, connection_points):
        self.neighbors[other_game] = connection_points

class GameGraph:
    '''GameGraph class to store the games and build the network.'''
    def __init__(self):
        self.games = {}  # This will store the game_id as key and the Game object as value

    def add_game(self, game):
        self.games[game.game_id] = game

    def calculate_connection_points(self, game1, game2):
        '''Calculate the connection points between two games based on shared attributes.'''
        connection_points = 0
        # Check for shared attributes and calculate connection points
        connection_points += 2 * len(set(game1.platforms) & set(game2.platforms))
        connection_points += 2 * len(set(game1.companies) & set(game2.companies))
        connection_points += 2 * len(set(game1.genres) & set(game2.genres))
        connection_points += 2 * len(set(game1.themes) & set(game2.themes))
        connection_points += len(set(game1.keywords) & set(game2.keywords))  # Keywords are less important
        return connection_points

    def build_network(self):
        # Calculate connection points for each pair of games and establish connections
        for game1 in self.games.values():
            for game2 in self.games.values():
                if game1.game_id != game2.game_id:
                    connection_points = self.calculate_connection_points(game1, game2)
                    # Pass the game ID instead of the Game object
                    game1.add_neighbor(game2, connection_points)

    def get_top_neighbors(self):
        # Sort the neighbors based on connection points and get the top 10 for each game
        for game in self.games.values():
            sorted_neighbors = sorted(game.neighbors.items(), key=lambda item: item[1], reverse=True)
            # Keep it as a dictionary, but only include the top 10
            game.neighbors = dict(sorted_neighbors[:10])


def main():
    pass

if __name__ == '__main__':
    main()
