import math


test_case = False


class MST:
    def __init__(self, nodes):
        self.nodes = nodes
        self.num_nodes = len(nodes)

    def _calculate_distance(self, point1, point2):
        """
        Returns Euclidian distance of 2 points
        :param point1:
        :param point2:
        :return:
        """
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    def _find(self, parent, i):
        """
        Find the root parent of a node with path compression
        :param parent:
        :param i:
        :return:
        """
        if parent[i] == i:
            return i
        else:
            parent[i] = self._find(parent, parent[i])
            return parent[i]

    def _union(self, parent, rank, x, y):
        """
        Union by rank
        :param parent:
        :param rank:
        :param x:
        :param y:
        :return:
        """
        root_x = self._find(parent, x)
        root_y = self._find(parent, y)

        if root_x != root_y:
            if rank[root_x] < rank[root_y]:
                parent[root_x] = root_y
            elif rank[root_x] > rank[root_y]:
                parent[root_y] = root_x
            else:
                parent[root_y] = root_x
                rank[root_x] += 1

    def CalculateMST(self):
        """
        Entry Point function. Will return the order of points
        :return:
        """
        edges = []
        for i in range(self.num_nodes):
            for j in range(i+1, self.num_nodes):
                dist = self._calculate_distance(self.nodes[i], self.nodes[j])
                edges.append((dist, i, j))

        edges.sort()

        parent = list(range(self.num_nodes))
        rank = [0] * self.num_nodes

        connected_points = []

        for dist, u, v in edges:
            root_u = self._find(parent, u)
            root_v = self._find(parent, v)

            # Prevent Cycles
            if root_u != root_v:
                connected_points.append([
                    int(self.nodes[u][0]), int(self.nodes[u][1]),
                    int(self.nodes[v][0]), int(self.nodes[v][1])
                ])

                self._union(parent, rank, root_u, root_v)

        return connected_points

"""

TEST CASE

"""
if __name__ == '__main__':
    if test_case:
        import random
        import matplotlib.pyplot as plt
        import numpy as np
        from scipy.spatial import distance
        from scipy.sparse.csgraph import minimum_spanning_tree

        num_nodes = 10  # Number of random nodes
        num_clusters = np.random.randint(2, 5)
        cluster_centre = np.random.uniform(100, 200, (num_clusters, 2))
        max_distance = 40
        min_distance = 20

        # Generate clustered random nodes
        nodes = []
        for _ in range(num_nodes):
            while True:
                if np.random.rand() > 0.5:
                    x = np.random.normal(150, max_distance)
                    y = np.random.normal(150, max_distance)
                else:
                    curr_cluster_idx = np.random.choice(num_clusters)
                    curr_cluster = cluster_centre[curr_cluster_idx]
                    x = np.random.normal(curr_cluster[0], max_distance)
                    y = np.random.normal(curr_cluster[1], max_distance)

                x = np.clip(x, 100, 200)
                y = np.clip(y, 100, 200)

                if len(nodes) == 0 or np.all(np.linalg.norm(np.array(nodes) - np.array([x, y]), axis=1) >= min_distance):
                    nodes.append([x, y])
                    break

        nodes = np.array(nodes)

        mst_instance = MST(nodes)
        my_mst = mst_instance.CalculateMST()

        dist_mat = distance.cdist(nodes, nodes, 'euclidean')
        scipy_mst_mat = minimum_spanning_tree(dist_mat).toarray().astype(bool)
        scipy_mst = []
        for i in range(len(nodes)):
            for j in range(i+1, len(nodes)):
                if scipy_mst_mat[i, j]:
                    scipy_mst.append([
                        int(nodes[i][0]),  int(nodes[i][1]),
                        int(nodes[j][0]), int(nodes[j][1])
                    ])

        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        axes[0].scatter(*zip(*nodes), color='blue')
        for x1, y1, x2, y2 in my_mst:
            axes[0].plot([x1, x2], [y1, y2], color='green')

        axes[0].set_title('MY MST')

        axes[1].scatter(*zip(*nodes), color='blue')
        for x1, y1, x2, y2 in scipy_mst:
            axes[1].plot([x1, x2], [y1, y2], color='red')
        axes[1].set_title('SCIPY MST')

        plt.show()

