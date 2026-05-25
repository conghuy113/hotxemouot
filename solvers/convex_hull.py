import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull

def giai_bai_toan_hinh_hoc_2_rb(opt_type, c_orig, constraints, x_conds):
    """
    Giải bài toán QHTT có ĐÚNG 2 RÀNG BUỘC bằng phương pháp hình học bao lồi vectơ.
    Giữ nguyên hệ số bài toán gốc, không qua các bước chuẩn hóa biến hoặc ràng buộc.
    """
    print("\n" + "="*66)
    print(" GIẢI BÀI TOÁN BẰNG PHƯƠNG PHÁP HÌNH HỌC TỔ HỢP LỒI TRỰC TIẾP")
    print("="*66)

    # Kiểm tra điều kiện số lượng ràng buộc
    if len(constraints) != 2:
        print(f"[!] Lỗi: Phương pháp này bắt buộc phải có ĐÚNG 2 ràng buộc. Bài toán hiện tại có {len(constraints)} ràng buộc.")
        return

    n_vars = len(c_orig)
    
    # Trích xuất trực tiếp ma trận hệ số A và vế phải b từ bài toán gốc
    A_orig = np.array([constraints[0]['A_row'], constraints[1]['A_row']], dtype=float)
    b_orig = np.array([constraints[0]['b'], constraints[1]['b']], dtype=float)
    c_orig = np.array(c_orig, dtype=float)

    # Tạo nhãn hiển thị cho các biến gốc ban đầu
    var_labels = [f"x{i+1}" for i in range(n_vars)]

    # 1. THIẾT LẬP PHƯƠNG TRÌNH TỔ HỢP LỒI (*) TRỰC TIẾP
    # h_j = a_1j + a_2j 
    h_coefficients = A_orig[0, :] + A_orig[1, :]
    K = b_orig[0] + b_orig[1]

    # Đảm bảo vế phải phương trình tổng hợp dương để tính tỉ lệ chính xác
    if K < 0 or (K == 0 and np.any(h_coefficients < 0)):
        h_coefficients = -h_coefficients
        K = -K

    print(f"\n___ PHƯƠNG TRÌNH TỔ HỢP LỒI (*) GỐC ___")
    str_th = " + ".join([f"({h_coefficients[j]:.2f})*{var_labels[j]}" for j in range(n_vars)])
    print(f"Hệ thức tổng hợp: {str_th} = {K:.2f}")
    print("-" * 30)

    # Tính toán các hệ số nhân multiplier M_j = K / h_j
    multipliers = []
    for j in range(n_vars):
        if abs(h_coefficients[j]) < 1e-9:
            multipliers.append(np.inf) # Xử lý trường hợp hệ số bằng 0
        else:
            multipliers.append(K / h_coefficients[j])

    # 2. XÁC ĐỊNH TỌA ĐỘ CÁC ĐIỂM VECTƠ a_j BAN ĐẦU
    points = []
    valid_points_idx = []
    
    print("Tọa độ các điểm vectơ trên mặt phẳng đồ thị:")
    for j in range(n_vars):
        mult = multipliers[j]
        if np.isinf(mult) or np.isnan(mult):
            print(f"  a_{j+1} ({var_labels[j]}) = (Không xác định do h_j = 0)")
            points.append((np.nan, np.nan))
            continue
            
        # Tọa độ điểm gốc tính theo công thức: x = a_2j * M_j, y = c_j * M_j
        x_coord = A_orig[1, j] * mult
        y_coord = c_orig[j] * mult
        points.append((x_coord, y_coord))
        valid_points_idx.append(j)
        print(f"  a_{j+1} ({var_labels[j]}) = ({x_coord:.3f}, {y_coord:.3f})")

    # Đường quét dọc ứng trực tiếp với vế phải b_2 của ràng buộc 2 gốc
    target_x = b_orig[1]
    print(f"\nĐường quét mục tiêu dọc: x = {target_x:.2f}")

    # 3. QUÉT GIAO ĐIỂM TRÊN BAO LỒI VECTƠ (Dựa theo loại tối ưu cực trị)
    is_max = opt_type.lower() == 'max'
    best_z = float('inf') if not is_max else float('-inf')
    best_pair = None
    best_lambdas = None

    for i in range(n_vars):
        if i not in valid_points_idx: continue
        for j in range(i + 1, n_vars):
            if j not in valid_points_idx: continue
            
            x1, y1 = points[i]
            x2, y2 = points[j]

            # Kiểm tra xem đường thẳng quét x = target_x có cắt qua đoạn thẳng [a_i, a_j] hay không
            if min(x1, x2) <= target_x <= max(x1, x2):
                M_mat = np.array([[1.0, 1.0], [x1, x2]])
                B_mat = np.array([1.0, target_x])
                try:
                    lambdas = np.linalg.solve(M_mat, B_mat)
                    # Điều kiện tổ hợp lồi: các hệ số lambda phải không âm
                    if np.all(lambdas >= -1e-9):
                        z_intersect = lambdas[0] * y1 + lambdas[1] * y2
                        
                        # Lựa chọn giao điểm tối ưu tùy thuộc bài toán thu về Min hay Max
                        if not is_max and z_intersect < best_z:
                            best_z = z_intersect
                            best_pair = (i, j)
                            best_lambdas = lambdas
                        elif is_max and z_intersect > best_z:
                            best_z = z_intersect
                            best_pair = (i, j)
                            best_lambdas = lambdas
                except np.linalg.LinAlgError:
                    continue

    if best_pair is None:
        print("\n[!] KẾT QUẢ: Không tìm thấy phương án tối ưu hợp lệ trên đồ thị phẳng! Miền nghiệm rỗng hoặc không giới nội.")
        return

    idx1, idx2 = best_pair
    print(f"-> Điểm tối ưu nằm trên đoạn biên nối giữa: [a_{idx1+1}, a_{idx2+1}]")

    # 4. PHÂN BỔ GIÁ TRỊ NGHIỆM GỐC TRỰC TIẾP
    final_x = np.zeros(n_vars)
    final_x[idx1] = best_lambdas[0] * multipliers[idx1]
    final_x[idx2] = best_lambdas[1] * multipliers[idx2]

    print("\n" + "="*50)
    print("KẾT LUẬN CUỐI CÙNG:")
    print("Bài toán có nghiệm tối ưu hình học trực tiếp:")
    for idx in range(n_vars):
        print(f"  x{idx+1} = {final_x[idx]:.4f}")

    print(f"\nGiá trị tối ưu {opt_type.capitalize()} Z = {best_z:.4f}")
    print("="*50 + "\n")

    # 5. VẼ ĐỒ THỊ BAO LỒI MINH HỌA AN TOÀN
    pts_arr = np.array([points[k] for k in valid_points_idx])
    plt.figure(figsize=(9, 7))
    plt.axhline(0, color='gray', linewidth=0.8, linestyle='--')
    plt.axvline(0, color='gray', linewidth=0.8, linestyle='--')

    # Vẽ vùng bao lồi nếu tập điểm không đồng phẳng
    if len(pts_arr) >= 3:
        try:
            hull = ConvexHull(pts_arr)
            plt.fill(pts_arr[hull.vertices, 0], pts_arr[hull.vertices, 1], 
                     alpha=0.15, color='orange', hatch='\\\\', label='Miền bao lồi hình học')
        except:
            pass

    # Vẽ các điểm nút và nhãn
    plt.scatter(pts_arr[:, 0], pts_arr[:, 1], color='blue', zorder=5)
    for k in valid_points_idx:
        xp, yp = points[k]
        plt.text(xp + 0.1, yp + 0.1, f"$a_{{{k+1}}}({var_labels[k]})$", fontsize=10, color='blue')

    # Minh họa đường quét ranh giới ràng buộc thứ 2 và giao điểm tối ưu
    plt.axvline(x=target_x, color='red', linestyle='-', linewidth=1.5, label=f'Đường cắt quét x = {target_x:.2f}')
    plt.scatter([target_x], [best_z], color='red', marker='*', s=200, zorder=6, label='Giao điểm tối ưu')

    plt.plot([points[idx1][0], points[idx2][0]], [points[idx1][1], points[idx2][1]], 
             color='purple', linewidth=3, label='Cạnh chứa nghiệm tối ưu')
             
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='upper right')
    plt.title("ĐỒ THỊ BAO LỒI VECTƠ")
    plt.show()