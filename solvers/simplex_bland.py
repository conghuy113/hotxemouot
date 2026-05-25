import numpy as np
import re

def get_var_priority(name):
    """
    Hàm trả về độ ưu tiên để chọn biến nhỏ nhất theo đúng Quy tắc Bland.
    Ưu tiên theo thứ tự tên biến: x1, x2... rồi mới tới w1, w2...
    """

    idx_match = re.search(r'\d+', name)
    idx = int(idx_match.group()) if idx_match else 999

    prefix = 0 if name.startswith('x') else 1

    suffix = 0
    if '+' in name:
        suffix = 1
    if '-' in name:
        suffix = 2
    if "'" in name:
        suffix = 3

    return (prefix, idx, suffix)


def giai_bai_toan_don_hinh_bland(
        opt_type,
        c_orig,
        constraints,
        x_conds):

    """
    Giải bài toán QHTT bằng thuật toán đơn hình
    áp dụng Quy tắc Bland chống lặp vòng.
    """

    print("\n" + "=" * 50)
    print("GIẢI BÀI TOÁN BẰNG THUẬT TOÁN ĐƠN HÌNH - QUY TẮC BLAND")
    print("=" * 50)

    # =====================================================
    # 1. CHUẨN HÓA BIẾN
    # =====================================================

    var_names_std = []

    c_std = []

    for i, cond in enumerate(x_conds):

        orig_idx = i + 1

        # x >= 0
        if cond == '>= 0':

            var_names_std.append(f"x{orig_idx}")

            c_std.append(c_orig[i])

        # x <= 0
        elif cond == '<= 0':

            var_names_std.append(f"x{orig_idx}'")

            c_std.append(-c_orig[i])

        # biến tự do
        elif cond == 'tự do':

            var_names_std.append(f"x{orig_idx}+")
            var_names_std.append(f"x{orig_idx}-")

            c_std.append(c_orig[i])
            c_std.append(-c_orig[i])

    is_max = opt_type.lower() == 'max'

    if is_max:
        c_std = [-val for val in c_std]

    # =====================================================
    # 2. CHUẨN HÓA RÀNG BUỘC
    # =====================================================

    A_std = []

    b_std = []

    for const in constraints:

        row_orig = const['A_row']

        sign = const['sign']

        rhs = const['b']

        row_std = []

        for i, cond in enumerate(x_conds):

            # x >= 0
            if cond == '>= 0':

                row_std.append(row_orig[i])

            # x <= 0
            elif cond == '<= 0':

                row_std.append(-row_orig[i])

            # biến tự do
            elif cond == 'tự do':

                row_std.append(row_orig[i])
                row_std.append(-row_orig[i])

        # <=
        if sign == '<=':

            A_std.append(row_std)

            b_std.append(rhs)

        # >=
        elif sign == '>=':

            A_std.append([-v for v in row_std])

            b_std.append(-rhs)

        # =
        elif sign == '=':

            A_std.append(row_std)
            b_std.append(rhs)

            A_std.append([-v for v in row_std])
            b_std.append(-rhs)

    # =====================================================
    # 3. KIỂM TRA VÔ NGHIỆM
    # =====================================================

    for i in range(len(b_std)):

        row = np.array(A_std[i])

        if np.all(np.abs(row) < 1e-9) and b_std[i] < -1e-9:

            print("\n" + "=" * 50)
            print("KẾT LUẬN CUỐI CÙNG:")
            print("Bài toán vô nghiệm.")
            print("=" * 50 + "\n")

            return

    # =====================================================
    # 4. KIỂM TRA NGHIỆM CƠ SỞ BAN ĐẦU
    # =====================================================

    if any(val < -1e-7 for val in b_std):

        print("[!] Phát hiện b_i < 0.")
        print("    Cần dùng Simplex 2 pha hoặc Big-M.")
        print("    Không thể áp dụng Bland cơ bản.")

        return

    num_constraints_std = len(b_std)

    num_vars_std = len(c_std)

    # =====================================================
    # 5. KHỞI TẠO TỪ VỰNG
    # =====================================================

    bas_vars = [
        f"w{i+1}"
        for i in range(num_constraints_std)
    ]

    non_bas_vars = list(var_names_std)

    dict_matrix = np.zeros(
        (num_constraints_std + 1,
         num_vars_std + 1)
    )

    dict_matrix[:num_constraints_std, :num_vars_std] = (
        -np.array(A_std)
    )

    dict_matrix[:num_constraints_std, -1] = b_std

    dict_matrix[-1, :num_vars_std] = c_std

    dict_matrix[-1, -1] = 0.0

    step = 0

    is_unbounded = False

    # =====================================================
    # 6. VÒNG LẶP SIMPLEX BLAND
    # =====================================================

    while True:

        print(f"\n___ TỪ VỰNG BLAND BƯỚC {step} ___")

        # ==============================================
        # In hàm mục tiêu
        # ==============================================

        z_label = "z'" if is_max else "z"

        z_str = (
            f"{z_label} = "
            f"{dict_matrix[-1, -1]:.2f}"
        )

        for j, nv in enumerate(non_bas_vars):

            v = dict_matrix[-1, j]

            if abs(v) > 1e-7:

                z_str += (
                    f" {'+' if v > 0 else '-'} "
                    f"{abs(v):.2f}*{nv}"
                )

        print(z_str.strip())

        print("-" * 30)

        # ==============================================
        # In các dòng cơ sở
        # ==============================================

        for i, bv in enumerate(bas_vars):

            r_str = (
                f"{bv} = "
                f"{dict_matrix[i, -1]:.2f}"
            )

            for j, nv in enumerate(non_bas_vars):

                v = dict_matrix[i, j]

                if abs(v) > 1e-7:

                    r_str += (
                        f" {'+' if v > 0 else '-'} "
                        f"{abs(v):.2f}*{nv}"
                    )

            print(r_str.strip())

        # ==============================================
        # CHỌN BIẾN VÀO
        # ==============================================

        c_curr = dict_matrix[-1, :-1]

        negative_indices = [
            j
            for j, val in enumerate(c_curr)
            if val < -1e-7
        ]

        # tối ưu
        if not negative_indices:

            break

        entering_idx = min(
            negative_indices,
            key=lambda j:
            get_var_priority(non_bas_vars[j])
        )

        # ==============================================
        # CHỌN BIẾN RA
        # ==============================================

        ratios = []

        valid_rows = []

        for i in range(num_constraints_std):

            coeff = dict_matrix[i, entering_idx]

            if coeff < -1e-7:

                ratios.append(
                    dict_matrix[i, -1]
                    / abs(coeff)
                )

                valid_rows.append(i)

            else:

                ratios.append(np.inf)

        # Không giới nội
        if (
            not valid_rows
            or np.min(ratios) == np.inf
        ):

            is_unbounded = True

            break

        min_ratio = np.min(ratios)

        best_rows = [
            i for i in valid_rows
            if abs(ratios[i] - min_ratio) < 1e-7
        ]

        leaving_row = min(
            best_rows,
            key=lambda i:
            get_var_priority(bas_vars[i])
        )

        print(
            f">> (Bland Pivot) "
            f"Biến vào: "
            f"{non_bas_vars[entering_idx]} | "
            f"Biến ra: "
            f"{bas_vars[leaving_row]}"
        )

        # ==============================================
        # PIVOT
        # ==============================================

        pivot_val = dict_matrix[
            leaving_row,
            entering_idx
        ]

        new_m = np.zeros_like(dict_matrix)

        # Dòng pivot
        new_m[
            leaving_row,
            entering_idx
        ] = 1.0 / pivot_val

        new_m[
            leaving_row,
            -1
        ] = (
            -dict_matrix[leaving_row, -1]
            / pivot_val
        )

        for j in range(len(non_bas_vars)):

            if j != entering_idx:

                new_m[
                    leaving_row,
                    j
                ] = (
                    -dict_matrix[leaving_row, j]
                    / pivot_val
                )

        # Các dòng khác
        for i in range(num_constraints_std + 1):

            if i != leaving_row:

                mul = dict_matrix[i, entering_idx]

                new_m[i, -1] = (
                    dict_matrix[i, -1]
                    + mul
                    * new_m[leaving_row, -1]
                )

                for j in range(len(non_bas_vars)):

                    if j != entering_idx:

                        new_m[i, j] = (
                            dict_matrix[i, j]
                            + mul
                            * new_m[leaving_row, j]
                        )

                new_m[i, entering_idx] = (
                    mul
                    * new_m[
                        leaving_row,
                        entering_idx
                    ]
                )

        # Hoán đổi biến
        bas_vars[leaving_row], non_bas_vars[entering_idx] = (
            non_bas_vars[entering_idx],
            bas_vars[leaving_row]
        )

        dict_matrix = new_m

        step += 1

    # =====================================================
    # 7. KẾT LUẬN
    # =====================================================

    print("\n" + "=" * 50)
    print("KẾT LUẬN CUỐI CÙNG:")

    # ==============================================
    # KHÔNG GIỚI NỘI
    # ==============================================

    if is_unbounded:

        print("Bài toán không giới nội (Unbounded).")

        if is_max:

            print("Giá trị tối ưu: Z = +∞")

        else:

            print("Giá trị tối ưu: Z = -∞")

        print("=" * 50 + "\n")

        return

    final_z = dict_matrix[-1, -1]

    opt_val = (
        -final_z
        if is_max
        else final_z
    )

    # =====================================================
    # KIỂM TRA VÔ SỐ NGHIỆM
    # =====================================================

    c_final = dict_matrix[-1, :-1]

    has_multiple = False

    for j in range(len(c_final)):

        # biến phi cơ sở có reduced cost = 0
        if abs(c_final[j]) < 1e-9:

            col = dict_matrix[:-1, j]

            # tồn tại hướng di chuyển
            if np.any(col < -1e-9):

                has_multiple = True

                break

    # =====================================================
    # VÔ SỐ NGHIỆM
    # =====================================================

    if has_multiple:

        print("Bài toán có vô số nghiệm tối ưu.")

        print(
            f"Giá trị tối ưu "
            f"{opt_type.capitalize()} "
            f"Z = {opt_val:.4f}"
        )

        print("=" * 50 + "\n")

        return

    # =====================================================
    # NGHIỆM DUY NHẤT
    # =====================================================

    print("Bài toán có nghiệm tối ưu duy nhất:")

    res = {
        v: 0.0
        for v in var_names_std
    }

    for i, v in enumerate(bas_vars):

        if v in res:

            res[v] = dict_matrix[i, -1]

    for i, cond in enumerate(x_conds):

        orig_idx = i + 1

        val = 0.0

        # x >= 0
        if cond == '>= 0':

            val = res.get(
                f"x{orig_idx}",
                0.0
            )

        # x <= 0
        elif cond == '<= 0':

            val = -res.get(
                f"x{orig_idx}'",
                0.0
            )

        # biến tự do
        elif cond == 'tự do':

            val = (
                res.get(f"x{orig_idx}+", 0.0)
                -
                res.get(f"x{orig_idx}-", 0.0)
            )

        print(f"  x{orig_idx} = {val:.4f}")

    print(
        f"\nGiá trị tối ưu "
        f"{opt_type.capitalize()} "
        f"Z = {opt_val:.4f}"
    )

    print("=" * 50 + "\n")