import pickle as pkl
import gzip as gz
import networkx as nx
import re

def load_problem(filename):
    # Đọc file sử dụng pickle và gzip
    with gz.open(filename, 'rb') as f:
        problem_file = pkl.load(f)
    return problem_file

def load_solution(solution_file):
    # Đọc file kết quả
    with open(solution_file, 'r') as file:
        lines = file.readlines()

    # Tạo dictionary để lưu giá trị của các phiLink và phiNode
    phiLink_values = {}
    phiNode_values = {}

    # Lặp qua các dòng trong file kết quả
    for line in lines:
        line = line.strip()
        if line.startswith("phiLink_s"):
            # Tách tên biến và giá trị
            variable_name, value, _ = line.split()
            # Lưu giá trị vào dictionary
            match = re.findall(r'_s(\d+)_\((\d+),_([^)]+)\)', variable_name)[0]
            sfc, link_S, link = match
            if sfc not in phiLink_values:
                phiLink_values[sfc] = {}
            phiLink_values[sfc][(link_S, link)] = int(value)
        elif line.startswith("phiNode_s"):
            # Tách tên biến và giá trị
            variable_name, value, _ = line.split()
            # Lưu giá trị vào dictionary
            sfc, node_S, node = variable_name.split('_')[1:]
            if sfc not in phiNode_values:
                phiNode_values[sfc] = {}
            phiNode_values[sfc][node_S] = int(value)
    
    return phiNode_values, phiLink_values

def validate_solution(phiNode_values, phiLink_values, G, SFCs):
    # Kiểm tra ràng buộc C1
    for node in G.nodes:
        sum_requirements = sum(
            phiNode_values.get(sfc, {}).get(node_S, 0) * nx.get_node_attributes(sfc, "Requirement").get(node_S, 0)
            for sfc in SFCs
            for node_S in sfc["nodes"]
        )
        capacity = nx.get_node_attributes(G, "Capacity").get(node, 0)
        if sum_requirements > capacity:
            # Ràng buộc không được thỏa mãn
            print(f"C1_i{node} không được thỏa mãn")
            return False

    # Kiểm tra ràng buộc C2
    for edge in G.edges:
        sum_requirements = sum(
            phiLink_values.get(sfc, {}).get(link_S, {}).get(edge, 0) * nx.get_edge_attributes(sfc, "Requirement").get(link_S, 0)
            for sfc in SFCs
            for link_S in sfc["edges"]
        )
        capacity = nx.get_edge_attributes(G, "Capacity").get(edge, 0)
        if sum_requirements > capacity:
            # Ràng buộc không được thỏa mãn
            print(f"C2_ij{edge} không được thỏa mãn")
            return False

    # Kiểm tra ràng buộc C3
    for sfc in SFCs:
        for node in G.nodes:
            sum_phiNode = sum(
                phiNode_values.get(sfc, {}).get(node_S, 0)
                for node_S in sfc["nodes"]
            )
            if sum_phiNode > 1:
                # Ràng buộc không được thỏa mãn
                print(f"C3_i{node}_s{SFCs.index(sfc)} không được thỏa mãn")
                return False

    # Kiểm tra ràng buộc C4
    for sfc in SFCs:
        for node_S in sfc["nodes"]:
            sum_phiNode = sum(
                phiNode_values.get(sfc, {}).get(node_S, 0)
                for node in G.nodes
            )
            if sum_phiNode != 1:
                # Ràng buộc không được thỏa mãn
                print(f"C4_v{node_S}_s{SFCs.index(sfc)} không được thỏa mãn")
                return False

    # Kiểm tra ràng buộc C5
    for sfc in SFCs:
        for edge_S in sfc["edges"]:
            for node in G.nodes:
                sum_phiLink_out = sum(
                    phiLink_values.get(sfc, {}).get(edge_S, {}).get((node, nodej), 0)
                    for nodej in G.nodes
                )
                sum_phiLink_in = sum(
                    phiLink_values.get(sfc, {}).get(edge_S, {}).get((nodej, node), 0)
                    for nodej in G.nodes
                )
                sum_phiNode_out = phiNode_values.get(sfc, {}).get(edge_S[0], {}).get(node, 0)
                sum_phiNode_in = phiNode_values.get(sfc, {}).get(edge_S[1], {}).get(node, 0)

                if sum_phiLink_out - sum_phiLink_in != sum_phiNode_out - sum_phiNode_in:
                    # Ràng buộc không được thỏa mãn
                    print(f"C5_s{SFCs.index(sfc)}_vw{edge_S}_i{node} không được thỏa mãn")
                    return False

    # Tất cả các ràng buộc được thỏa mãn
    print("Tất cả các ràng buộc được thỏa mãn")
    return True

def validate(problem_file, solution_file):
    # Load thông tin từ tệp problem
    problem_data = load_problem(problem_file)
    G = problem_data["PHYGraph"]
    SFCs = problem_data["SFCsList"]
    
    # Load giải pháp từ tệp solution
    phiNode_values, phiLink_values = load_solution(solution_file)
    
    # Kiểm tra giải pháp
    constraints_satisfied = validate_solution(phiNode_values, phiLink_values, G, SFCs)

    if constraints_satisfied:
        print("Tất cả các ràng buộc được thỏa mãn")
    else:
        print("Có ràng buộc không được thỏa mãn")

if __name__=="__main__":
    problem_file = "demo_multiple_mapping_1.dat"
    solution_file = "demo_multiple_mapping_4.mps.sol"
    validate(problem_file, solution_file)
