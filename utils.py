# utils.py
import numpy as np
import matplotlib.pyplot as plt
import math
import re

# ==========================================
# 1. CÁC HÀM CHUYỂN ĐỔI BÀI TOÁN
# ==========================================

def chuyen_sang_dang_chuan(opt_type, c_orig, constraints, x_conds):
    """
    Chuyển bài toán tổng quát về dạng chuẩn (Min, <=, x >= 0).
    """
    c_std = []
    var_names_std = []

    # Xử lý biến và Hàm mục tiêu
    for i, cond in enumerate(x_conds):
        orig_idx = i + 1
        if cond == '>= 0':
            var_names_std.append(f"x{orig_idx}")
            c_std.append(c_orig[i])
        elif cond == '<= 0':
            var_names_std.append(f"x{orig_idx}'")
            c_std.append(-c_orig[i])
        elif cond == 'tự do':
            var_names_std.append(f"x{orig_idx}+")
            c_std.append(c_orig[i])
            var_names_std.append(f"x{orig_idx}-")
            c_std.append(-c_orig[i])

    if opt_type.lower() == 'max':
        c_std = [-val for val in c_std]

    # Xử lý các ràng buộc (Ma trận A và Vector b)
    A_std = []
    b_std = []
    for const in constraints:
        row_orig = const['A_row']
        sign = const['sign']
        rhs = const['b']

        row_std = []
        for i, cond in enumerate(x_conds):
            if cond == '>= 0': row_std.append(row_orig[i])
            elif cond == '<= 0': row_std.append(-row_orig[i])
            elif cond == 'tự do':
                row_std.append(row_orig[i])
                row_std.append(-row_orig[i])

        if sign == '<=':
            A_std.append(row_std)
            b_std.append(rhs)
        elif sign == '>=':
            A_std.append([-v for v in row_std])
            b_std.append(-rhs)
        elif sign == '=':
            A_std.append(row_std)
            b_std.append(rhs)
            A_std.append([-v for v in row_std])
            b_std.append(-rhs)

    return c_std, A_std, b_std, var_names_std


def chuyen_tong_quat_sang_chinh_tac(opt_type, c_orig, constraints, x_conds):
    """
    Chuyển bài toán từ dạng Tổng quát trực tiếp sang Chính tắc: Min, Ax = b, x >= 0.
    """
    c_std = []
    var_names_std = []
    for i, cond in enumerate(x_conds):
        orig_idx = i + 1
        if cond == '>= 0':
            var_names_std.append(f"x{orig_idx}")
            c_std.append(c_orig[i])
        elif cond == '<= 0':
            var_names_std.append(f"x{orig_idx}'")
            c_std.append(-c_orig[i])
        elif cond == 'tự do':
            var_names_std.append(f"x{orig_idx}+")
            c_std.append(c_orig[i])
            var_names_std.append(f"x{orig_idx}-")
            c_std.append(-c_orig[i])

    if opt_type.lower() == 'max':
        c_std = [-val for val in c_std]

    A_final = []
    b_final = []
    num_constraints = len(constraints)
    slack_matrix = [[0.0] * num_constraints for _ in range(num_constraints)]

    for i, const in enumerate(constraints):
        row_orig = const['A_row']
        sign = const['sign']
        rhs = const['b']

        row_std = []
        for j, cond in enumerate(x_conds):
            if cond == '>= 0': row_std.append(row_orig[j])
            elif cond == '<= 0': row_std.append(-row_orig[j])
            elif cond == 'tự do':
                row_std.append(row_orig[j])
                row_std.append(-row_orig[j])

        if sign == '<=':
            slack_matrix[i][i] = 1.0
            A_final.append(row_std)
            b_final.append(rhs)
        elif sign == '>=':
            slack_matrix[i][i] = -1.0
            A_final.append(row_std)
            b_final.append(rhs)
        elif sign == '=':
            A_final.append(row_std)
            b_final.append(rhs)

    for i in range(len(A_final)):
        A_final[i] = A_final[i] + slack_matrix[i]

    c_final = c_std + [0.0] * num_constraints
    var_names_final = var_names_std + [f"w{i+1}" for i in range(num_constraints)]

    return c_final, A_final, b_final, var_names_final


# ==========================================
# 2. CÁC HÀM XỬ LÝ SẮP XẾP VÀ QUY TẮC
# ==========================================

def get_var_priority(name):
    """Quy tắc Bland: Ưu tiên theo thứ tự tên biến: x1, x2... rồi tới w1, w2..."""
    idx_match = re.search(r'\d+', name)
    idx = int(idx_match.group()) if idx_match else 999

    prefix = 0 if name.startswith('x') else 1
    suffix = 0
    if '+' in name: suffix = 1
    if '-' in name: suffix = 2
    if "'" in name: suffix = 3

    return (prefix, idx, suffix)

def var_sort_key(var_name):
    """Quy tắc Alpha để sắp xếp biến, xử lý được cả x1', x1+, x1-"""
    if var_name == 'x0': return (3, 0, '')
    match = re.match(r"([xw])(\d+)(.*)", var_name)
    if not match: return (4, 0, '')
    v_type, num, suffix = match.groups()
    type_order = 1 if v_type == 'x' else 2
    return (type_order, int(num), suffix)


# ==========================================
# 3. CÁC HÀM IN ẤN VÀ KẾT LUẬN
# ==========================================

def in_bang_don_hinh(step, table, row_labels, col_labels):
    """In bảng đơn hình dạng bảng theo định dạng tiêu chuẩn"""
    print(f"\n___ BẢNG ĐƠN HÌNH BƯỚC {step} ___")
    header = ["Cơ sở"] + col_labels + ["b"]
    print(f"{' | '.join([f'{h:>10}' for h in header])}")
    print("-" * (12 * len(header)))

    for i, row in enumerate(table):
        row_str = [f"{row_labels[i]:>10}"]
        for val in row:
            clean_val = 0.0 if abs(val) < 1e-9 else val
            row_str.append(f"{clean_val:>10.2f}")
        print(f"{' | '.join(row_str)}")
    print("-" * (12 * len(header)))


def in_tu_vung(step, basis, non_basis, dict_b, dict_A, obj_v, obj_C, obj_name):
    """Hàm in từ vựng từng bước (Hàm mục tiêu in trước)"""
    print(f"\n___ TỪ VỰNG BƯỚC {step} ___")
    sorted_nb = sorted(non_basis, key=var_sort_key)
    sorted_b = sorted(basis, key=var_sort_key)

    terms = []
    for nb_var in sorted_nb:
        coeff = obj_C[nb_var]
        if abs(coeff) > 1e-7:
            sign = "+" if coeff > 0 else "-"
            terms.append(f"{sign} {abs(coeff):.2f}*{nb_var}")
    terms_str = " ".join(terms) if terms else ""
    print(f"{obj_name} = {obj_v:.2f} {terms_str}".strip())
    print("-" * 30)

    for b_var in sorted_b:
        terms = []
        for nb_var in sorted_nb:
            coeff = dict_A[b_var][nb_var]
            if abs(coeff) > 1e-7:
                sign = "+" if coeff > 0 else "-"
                terms.append(f"{sign} {abs(coeff):.2f}*{nb_var}")
        terms_str = " ".join(terms) if terms else ""
        print(f"{b_var} = {dict_b[b_var]:.2f} {terms_str}".strip())


def in_ket_luan(opt_type, Z_v, basis, dict_b, var_names, x_conds):
    """Khôi phục nghiệm từ biến đã chuẩn hóa về biến gốc ban đầu."""
    print("\n" + "="*50)
    print("KẾT LUẬN CUỐI CÙNG:")
    print("Bài toán có nghiệm tối ưu:")

    sol_std = {v: 0.0 for v in var_names}
    for b_var in basis:
        if b_var in sol_std:
            sol_std[b_var] = dict_b[b_var]

    for i, cond in enumerate(x_conds):
        orig_idx = i + 1
        val = 0.0
        if cond == '>= 0':
            val = sol_std.get(f"x{orig_idx}", 0.0)
        elif cond == '<= 0':
            val = -sol_std.get(f"x{orig_idx}'", 0.0)
        elif cond == 'tự do':
            val = sol_std.get(f"x{orig_idx}+", 0.0) - sol_std.get(f"x{orig_idx}-", 0.0)
        print(f"  x{orig_idx} = {val:.4f}")

    final_z = -Z_v if opt_type.lower() == 'max' else Z_v
    print(f"\nGiá trị tối ưu {opt_type.capitalize()} Z = {final_z:.4f}")
    print("="*50 + "\n")


# ==========================================
# 4. HÀM XOAY TRỤC (PIVOT) CHO TỪ VỰNG
# ==========================================

def pivot(basis, non_basis, dict_b, dict_A, W_v, W_C, Z_v, Z_C, enter, leave):
    """Thực hiện phép xoay biến (Pivot)"""
    a_le = dict_A[leave][enter]
    new_basis = [enter if v == leave else v for v in basis]
    new_non_basis = [leave if v == enter else v for v in non_basis]
    new_b = {}
    new_A = {v: {} for v in new_basis}

    new_b[enter] = -dict_b[leave] / a_le
    new_A[enter][leave] = 1.0 / a_le
    for j in non_basis:
        if j != enter:
            new_A[enter][j] = -dict_A[leave][j] / a_le

    for i in basis:
        if i != leave:
            a_ie = dict_A[i][enter]
            new_b[i] = dict_b[i] + a_ie * new_b[enter]
            new_A[i][leave] = a_ie * new_A[enter][leave]
            for j in non_basis:
                if j != enter:
                    new_A[i][j] = dict_A[i][j] + a_ie * new_A[enter][j]

    new_W_v, new_W_C = W_v, {}
    if W_C:
        w_ce = W_C.get(enter, 0.0)
        new_W_v = W_v + w_ce * new_b[enter]
        new_W_C[leave] = w_ce * new_A[enter][leave]
        for j in non_basis:
            if j != enter:
                new_W_C[j] = W_C.get(j, 0.0) + w_ce * new_A[enter][j]

    new_Z_v, new_Z_C = Z_v, {}
    if Z_C is not None:
        z_ce = Z_C.get(enter, 0.0)
        new_Z_v = Z_v + z_ce * new_b[enter]
        new_Z_C[leave] = z_ce * new_A[enter][leave]
        for j in non_basis:
            if j != enter:
                new_Z_C[j] = Z_C.get(j, 0.0) + z_ce * new_A[enter][j]

    return new_basis, new_non_basis, new_b, new_A, new_W_v, new_W_C, new_Z_v, new_Z_C


# ==========================================
# 5. CÁC HÀM HỖ TRỢ VẼ ĐỒ THỊ
# ==========================================

def get_lcm(a, b):
    """Tìm Bội chung nhỏ nhất (phục vụ việc vẽ đường hướng mục tiêu ban đầu)"""
    if a == 0 or b == 0: return max(abs(a), abs(b), 1)
    scale = 100
    ia, ib = int(abs(a) * scale), int(abs(b) * scale)
    gcd = math.gcd(ia, ib)
    return (ia * ib) / gcd / scale

def ve_hinh_2d(c_coeffs, constraints, res, opt_type, bounds):
    """Vẽ đồ thị miền nghiệm và đường hàm mục tiêu"""
    max_v = 15
    if res.status == 0:
        max_v = max(max(res.x), 10) * 1.5

    d = np.linspace(0, max_v, 500)
    X, Y = np.meshgrid(d, d)
    plt.figure(figsize=(10, 8))

    feasible_mask = np.ones_like(X, dtype=bool)

    if bounds[0][0] == 0: feasible_mask &= (X >= 0)
    if bounds[0][1] == 0: feasible_mask &= (X <= 0)
    if bounds[1][0] == 0: feasible_mask &= (Y >= 0)
    if bounds[1][1] == 0: feasible_mask &= (Y <= 0)

    for const in constraints:
        row = const['A_row']
        sign = const['sign']
        rhs = const['b']

        if sign == "<=":
            feasible_mask &= (row[0]*X + row[1]*Y <= rhs + 1e-7)
        elif sign == ">=":
            feasible_mask &= (row[0]*X + row[1]*Y >= rhs - 1e-7)
        elif sign == "=":
            feasible_mask &= (np.abs(row[0]*X + row[1]*Y - rhs) < 0.05)

    plt.imshow(feasible_mask.astype(int), extent=(0, max_v, 0, max_v),
               origin="lower", cmap="Greens", alpha=0.3)

    for i, const in enumerate(constraints):
        row = const['A_row']
        sign = const['sign']
        rhs = const['b']
        label = f'RB{i+1}: {row[0]}x1 + {row[1]}x2 {sign} {rhs}'

        if row[1] != 0:
            plt.plot(d, (rhs - row[0]*d)/row[1], label=label)
        else:
            if row[0] != 0:
                plt.axvline(x=rhs/row[0], label=label)

    lcm_val = get_lcm(c_coeffs[0], c_coeffs[1])
    if c_coeffs[1] != 0:
        plt.plot(d, (lcm_val - c_coeffs[0]*d)/c_coeffs[1], 'b:',
                 linewidth=1.5, alpha=0.6, label=f'Hướng song song của Z')

    if res.status == 0:
        plt.plot(res.x[0], res.x[1], 'ro', markersize=8, label='Nghiệm tối ưu')
        plt.annotate(f'({res.x[0]:.2f}, {res.x[1]:.2f})', (res.x[0], res.x[1]),
                     xytext=(10,10), textcoords='offset points', color='red', weight='bold')

    opt_val_goc = c_coeffs[0]*res.x[0] + c_coeffs[1]*res.x[1]
    if c_coeffs[1] != 0:
        plt.plot(d, (opt_val_goc - c_coeffs[0]*d)/c_coeffs[1], 'r-',
                 linewidth=2, label=f'Đường tối ưu Z={opt_val_goc:.2f}')
    else:
        plt.axvline(x=opt_val_goc/c_coeffs[0], color='r', linewidth=2, label=f'Đường tối ưu Z={opt_val_goc:.2f}')

    plt.title(f"Phương pháp Đồ thị ({opt_type.capitalize()} Z)\n{res.message}")
    plt.xlim(0, max_v); plt.ylim(0, max_v)
    plt.xlabel('x1'); plt.ylabel('x2')
    plt.axhline(0, color='black', lw=1); plt.axvline(0, color='black', lw=1)
    plt.legend(loc='upper right', fontsize='small')
    plt.grid(True, alpha=0.3)
    plt.show()