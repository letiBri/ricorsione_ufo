import copy

from database.DAO import DAO
import networkx as nx  # libreria usata per gestire i grafi

from model.sighting import Sighting


class Model:
    def __init__(self):
        self._grafo = nx.DiGraph()
        self._nodes = []
        self._cammino_ottimo = []  # salvo la soluzione ottima
        self._score_ottimo = 0  # salvo il punteggio migliore

    def get_years(self):
        return DAO.get_years()

    def get_shapes_year(self, year: int):
        return DAO.get_shapes_year(year)

    def create_graph(self, year: int, shape: str):
        self._grafo.clear()
        self._nodes = DAO.get_nodes(year, shape)
        self._grafo.add_nodes_from(self._nodes)

        # calcolo degli edges in modo programmatico
        for i in range(0, len(self._nodes) - 1):
            for j in range(i + 1, len(self._nodes)):
                if self._nodes[i].state == self._nodes[j].state and self._nodes[i].longitude < self._nodes[j].longitude:
                    weight = self._nodes[j].longitude - self._nodes[i].longitude
                    self._grafo.add_edge(self._nodes[i], self._nodes[j], weight=weight)
                elif self._nodes[i].state == self._nodes[j].state and self._nodes[i].longitude > self._nodes[j].longitude:
                    weight = self._nodes[i].longitude - self._nodes[j].longitude
                    self._grafo.add_edge(self._nodes[j], self._nodes[i], weight=weight)

    def get_top_edges(self):
        sorted_edges = sorted(self._grafo.edges(data=True), key=lambda edge: edge[2].get('weight'), reverse=True)
        return sorted_edges[0:5]


    def get_nodes(self):
        return self._grafo.nodes()

    # def get_edges(self):
    #     return list(self._grafo.edges(data=True))

    def get_num_of_nodes(self):
        return self._grafo.number_of_nodes()

    def get_num_of_edges(self):
        return self._grafo.number_of_edges()

    def cammino_ottimo(self):
        self._cammino_ottimo = []  # resetto la soluzione ottima
        self._score_ottimo = 0  # azzero il punteggio
        for node in self._grafo.nodes():
            parziale = [node]
            rimanenti = self.calcola_rimanenti(parziale)
            self._ricorsione(parziale, rimanenti)
        return self._cammino_ottimo, self._score_ottimo

    def _ricorsione(self, parziale, nodi_rimanenti):  # parziale è una lista di nodi, nodi_rimanenti sono quelli da cui peschiamo
        # la condizione terminale è definita dal fatto se non ho più nodi che posso raggiungere
        # caso terminale
        if len(nodi_rimanenti) == 0:
            punteggio = self.calcolo_punteggio(parziale)
            if punteggio > self._score_ottimo:
                self._score_ottimo = punteggio  # aggiorno il punteggio ottimo
                self._cammino_ottimo = copy.deepcopy(parziale)  # aggiorno la soluzione ottima
                print(self._cammino_ottimo)
        # caso ricorsivo
        else:
            # per ogni nodo rimanente
            for nodo in nodi_rimanenti:
                # aggiungere il nodo
                parziale.append(nodo)
                # calcolare i nuovi rimanenti di questo nodo
                nuovi_rimanenti = self.calcola_rimanenti(parziale)
                # andare avanti nella ricorsione
                self._ricorsione(parziale, nuovi_rimanenti)
                # backtracking
                parziale.pop()

    def calcolo_punteggio(self, parziale):
        punteggio = 0
        # termine fisso
        punteggio += 100 * len(parziale)  # aggiungo 100 per ogni nodo del parziale
        # termine variabile
        for i in range(1, len(parziale)):
            if parziale[i].datetime.month == parziale[i-1].datetime.month:  # aggiungo 200 se due avvistamenti successivi sono avvenuti nello stesso mese
                punteggio += 200
        return punteggio

    def calcola_rimanenti(self, parziale):
        nuovi_rimanenti = []
        # prendiamo i nodi successivi
        for i in self._grafo.successors(parziale[-1]):  # successors() restituisce un oggetto iterator: dato un nodo, cioè l'ultimo messo nel parziale, la funzione trova i successivi
            # di questi nodi, dobbiamo verificare il vincolo sul mese
            if self.is_vincolo_ok(parziale, i) and self.is_vincolo_durata_ok(parziale, i):
                nuovi_rimanenti.append(i)
        return nuovi_rimanenti

    def is_vincolo_durata_ok(self, parziale, nodo: Sighting):
        return nodo.duration > parziale[-1].duration  # strettamente crescente

    def is_vincolo_ok(self, parziale, nodo: Sighting):  # suggerisco all'editor che il nodo è un oggetto Sighting
        mese = nodo.datetime.month
        counter = 0
        for i in parziale:
            if i.datetime.month == mese:
                counter += 1
        if counter >= 3:
            return False
        return True
