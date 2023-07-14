def validate_constraints(solution_file, G, SFCs, phiNode_S, phiLink_S):
    # Đọc file kết quả
    with open(solution_file, 'r') as file:
        lines = file.readlines()
    
    # Tạo dictionary để lưu giá trị của các phiLink và phiNode
    phiLink_values = {}
    phiNode_values = {}
    
    # Hàm kiểm tra sự tồn tại của biến và trả về giá trị
    def get_variable_value(variable_name, dictionary, default_value=0):
        _, s, *var = variable_name.split('_')
        s = str(int(s))  # Chuyển s thành chuỗi
        return dictionary.get(s, {}).get('_'.join(var), default_value)
    
    # Lặp qua các dòng trong file kết quả
    for line in lines:
        line = line.strip()
        if line.startswith("phiLink_s"):
            # Tách tên biến và giá trị
            variable_name, value, _ = line.split()
            # Lưu giá trị vào dictionary
            sfc, link_S, link = variable_name.split('_')[1:]
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
    
    # Kiểm tra ràng buộc C1
    for node in G.nodes:
        sum_requirements = sum(
            get_variable_value(f"phiNode_s{str(s)}_{node_S}", phiNode_values) *
            nx.get_node_attributes(sfc, "Requirement").get(node, 0)
            for s, sfc in enumerate(SFCs)
            for node_S in sfc.nodes
        )
        capacity = nx.get_node_attributes(G, "Capacity").get(node, 0)
        if sum_requirements > capacity:
            # Ràng buộc không được thỏa mãn
            print(f"C1_i{node} không được thỏa mãn")
            return False
    
    # Kiểm tra ràng buộc C2
    for edge in G.edges:
        sum_requirements = sum(
            get_variable_value(f"phiLink_s{str(s)}_{link_S}_{link}", phiLink_values) *
            nx.get_edge_attributes(sfc, "Requirement").get((link_S, link), 0)
            for s, sfc in enumerate(SFCs)
            for link_S, link in sfc.edges
        )
        capacity = nx.get_edge_attributes(G, "Capacity").get(edge, 0)
        if sum_requirements > capacity:
            # Ràng buộc không được thỏa mãn
            print(f"C2_ij{edge} không được thỏa mãn")
            return False
    
    # Kiểm tra ràng buộc C3
    for s, sfc in enumerate(SFCs):
        for node in G.nodes:
            sum_phiNode = sum(
                get_variable_value(f"phiNode_s{str(s)}_{node_S}", phiNode_values)
                for node_S in sfc.nodes
            )
            if sum_phiNode > 1:
                # Ràng buộc không được thỏa mãn
                print(f"C3_i{node}_s{s} không được thỏa mãn")
                return False
    
    # Kiểm tra ràng buộc C4
    for s, sfc in enumerate(SFCs):
        for node_S in sfc.nodes:
            sum_phiNode = sum(
                get_variable_value(f"phiNode_s{str(s)}_{node_S}", phiNode_values)
                for node in G.nodes
            )
            if sum_phiNode != 1:
                # Ràng buộc không được thỏa mãn
                print(f"C4_v{node_S}_s{s} không được thỏa mãn")
                return False
    
    # Kiểm tra ràng buộc C5
    for s, sfc in enumerate(SFCs):
        for edge_S in sfc.edges:
            for node in G.nodes:
                sum_phiLink_out = sum(
                    get_variable_value(f"phiLink_s{str(s)}_{edge_S[0]}_{nodej}", phiLink_values)
                    for nodej in G.nodes
                )
                sum_phiLink_in = sum(
                    get_variable_value(f"phiLink_s{str(s)}_{nodej}_{edge_S[1]}", phiLink_values)
                    for nodej in G.nodes
                )
                sum_phiNode_diff = (
                    get_variable_value(f"phiNode_s{str(s)}_{edge_S[0]}", phiNode_values) -
                    get_variable_value(f"phiNode_s{str(s)}_{edge_S[1]}", phiNode_values)
                )
                if sum_phiLink_out - sum_phiLink_in != sum_phiNode_diff:
                    # không được thỏa mãn
                    print(f"Ràng buộc C5_s{s}_vw{edge_S}_i{node} không được thỏa mãn")
                    return False
    
    # Các ràng buộc được thỏa mãn
    print("Tất cả được thỏa mãn")
    return True
