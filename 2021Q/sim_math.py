import sys

class Instance:
    def __init__(self, file):
        self.file_name = file
        with open(file) as f:
            self.D, self.I, self.S, self.V, self.F = map(int,next(f).strip().split())
            self.streets = {}
            for _ in range(self.S):
                B,E,name,L = next(f).strip().split()
                self.streets[name] = (int(B),int(E),int(L))
            self.paths = []
            for _ in range(self.V):
                p = list(next(f).strip().split())[1:]
                self.paths.append(p)

    @staticmethod
    def from_argv():
        return Instance(sys.argv[1])

    def score_upperbound(self):
        return self.V * (self.F + self.D)


from collections import deque, defaultdict

class Solution:
    def __init__(self, solution, instance):
        assert isinstance(instance, Instance)
        self.instance = instance
        # typecheck the solution

        # solution = list(
        #   (intersection_id, list((street, time),....),
        #   (inte...)
        #   )
        allowed_streets = set(instance.streets.keys())
        assert type(solution) == list
        found_intersections = set()
        for intersection in solution:
            assert type(intersection) == tuple
            assert len(intersection) == 2
            iid, streets = intersection
            assert type(iid) == int
            assert iid not in found_intersections
            found_intersections.add(iid)
            assert 0<= iid < instance.I
            assert type(streets) == list
            found_streets = set()
            for street in streets:
                assert len(street) == 2
                sn, time = street
                assert sn in allowed_streets
                assert type(sn) == str
                assert sn not in found_streets
                assert type(time) == int
                assert 1<= time<= instance.D
                found_streets.add(sn)

        self.solution = solution


    @staticmethod
    def from_file(file, instance):
        with open(file) as f:
            solution = list() # parse solution from file\

            for _ in range(int(f.readline())):
                iid = int(f.readline())
                streets =[]
                for _ in range(int(f.readline())):
                    sn, time = f.readline().split(" ")
                    streets.append((sn,int(time)))
                solution.append((iid, streets))
        return Solution(solution, instance)


    @staticmethod
    def from_argv(instance = None):
        n_argv = 1
        if instance is None:
            instance = Instance.from_argv()
            n_argv += 1
        return Solution.from_file(sys.argv[n_argv], instance)

    def score(self, show_streets= False):
        from timeit import default_timer as timer


        # intersections = []
        # for intersection in range(self.instance.I):
        #     intersections.append([street for street in self.instance.streets if self.instance.streets[street][1] == intersection])

        # Construct a data structure for each intersection and street to indicate whether the intersection is available.

        # intersection_busy = [[False for _ in self.instance.D] for iid, streets in self.solution]

        print('Constructing data structure.')
        start = timer()
        intersection_available_from_street_at_time = [dict() for _ in range(self.instance.I)]
        for iid, streets in self.solution:
            start_time = 0
            end_time = -1
            cycle_length = sum([street[1] for street in streets])
            for index, street in enumerate(streets):
                end_time += street[1]
                intersection_available_from_street_at_time[iid][street[0]] = [t for t in range(self.instance.D) if (t % cycle_length) >= start_time and (t % cycle_length) <= end_time]
                # print(iid, street, start_time, end_time, cycle_length, intersection_available_from_street_at_time[iid][street[0]])
                start_time = end_time + 1
        end = timer()
        print('Took ', end - start, ' seconds.')
        #Create car class for simplification.
        class Car:
            def __init__(self, id):
                self.id = id
                self.path_index = 0
                self.time_at_green_light  = 0

            def __str__(self):
                return '[id: ' + str(self.id) + ', pid:' + str(self.path_index) + ', time: ' + str(self.time_at_green_light) +  ']'

        # Create buckets to store the cars for each timestep.
        time_buckets = [[] for t in range(self.instance.D)]

        # Initialise the initial placement of the cars.
        print('Initialise the buckets.')
        start = timer()
        cars = [Car(v) for v in range(self.instance.V)]
        for car in cars:
            street = self.instance.paths[car.id][car.path_index]
            iid = self.instance.streets[street][1]
            if street in intersection_available_from_street_at_time[iid] and len(intersection_available_from_street_at_time[iid][street]):
                car.time_at_green_light = min(intersection_available_from_street_at_time[iid][street])
                intersection_available_from_street_at_time[iid][street].remove(car.time_at_green_light)
                time_buckets[car.time_at_green_light].append(car)
        end = timer()
        print('Took ', end - start, ' seconds.')
        # Iterate over the buckets.
        print('Iterate over the buckets.')
        start = timer()
        score = 0
        completions = 0
        for t in range(self.instance.D):
            # if not t % 1:
            #     print('Iteration', t, '.....\r')
            for car in time_buckets[t]:
                car.path_index += 1
                street = self.instance.paths[car.id][car.path_index]
                iid, length = self.instance.streets[street][1:]
                if car.path_index < len(self.instance.paths[car.id]) - 1:
                    # print('car not yet at end.')
                    if street in intersection_available_from_street_at_time[iid]:
                        # print('light can be green')
                        for index, time in enumerate(intersection_available_from_street_at_time[iid][street]):
                            if time >= t + length:
                                # print('Found a spot!')
                                car.time_at_green_light = time
                                intersection_available_from_street_at_time[iid][street].pop(index)
                                time_buckets[car.time_at_green_light].append(car)
                                break;
                else:
                    # print('Iteration ', t, car, street, iid, length)
                    if car.time_at_green_light < self.instance.D + 1:
                        score += self.instance.F + (self.instance.D - car.time_at_green_light - length)
                        completions += 1
        end = timer()
        print('Took ', end - start, ' seconds.')
        # print('Total completions ', completions, '/', len(cars))
        return score

    def write(self):
        import os
        score = self.score()
        print(f"New score is {score} which is {score/self.instance.score_upperbound()*100}% of upperbound.")
        file_name = f"{os.path.split(self.instance.file_name)[-1][0]}_{score}.out"
        file_path = os.path.join("output", file_name)

        with open(file_path, "w") as f:
            f.write(f"{len(self.solution)}\n")
            for iid, streets in self.solution:
                f.write(f"{iid}\n")
                f.write(f"{len(streets)}\n")
                for sn, time in streets:
                    f.write(f"{sn} {time}\n")
            # write this to file


if __name__ == "__main__":
    print(Solution.from_argv().score(True))
