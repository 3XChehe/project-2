def find_position_3d(current_raw_rssi, k=3):
    if not fingerprint_db:
        return current_pos[0], current_pos[1], current_pos[2]
        
    # CHUẨN HÓA VECTOR RSSI THỜI GIAN THỰC ĐANG NHẬN ĐƯỢC
    current_normalized = normalize_rssi(current_raw_rssi)
    
    distances = []
    for coord, db_normalized_vector in fingerprint_db.items():
        if len(db_normalized_vector) < 3: continue
        
        # Tính khoảng cách Euclidean giữa 2 vector ĐÃ CHUẨN HÓA
        dist = np.sqrt(sum((current_normalized[i] - db_normalized_vector[i])**2 for i in range(3)))
        distances.append((dist, coord))
    
    if not distances:
        return current_pos[0], current_pos[1], current_pos[2]
    
    # Sắp xếp tìm K điểm láng giềng gần nhất
    distances.sort(key=lambda x: x[0])
    neighbors = distances[:k]
    
    # Tính toán vị trí theo trọng số nghịch đảo khoảng cách (WKNN)
    total_w = sum(1.0 / (d[0] + 0.0001) for d in neighbors) # Tránh lỗi chia cho 0
    
    final_x = sum(n[1][0] * (1.0 / (n[0] + 0.0001)) for n in neighbors) / total_w
    final_y = sum(n[1][1] * (1.0 / (n[0] + 0.0001)) for n in neighbors) / total_w
    final_z = sum(n[1][2] * (1.0 / (n[0] + 0.0001)) for n in neighbors) / total_w
    
    return final_x, final_y, final_z
