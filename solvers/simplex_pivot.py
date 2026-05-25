import numpy as np

def giai_bai_toan_xoay_don_hinh(
        opt_type,
        c_orig,
        constraints,
        x_conds):

    """
    Giải bài toán QHTT bằng
    THUẬT TOÁN XOAY ĐƠN HÌNH THÔNG THƯỜNG
    """

    print("\n" + "="*50)
    print("GIẢI BÀI TOÁN BẰNG THUẬT TOÁN XOAY ĐƠN HÌNH")
    print("="*50)

    # =====================================================
    # 1. CHUẨN HÓA BIẾN
    # =====================================================

    var_names = []

    mapping = []

    c_std = []

    current_idx = 0

    for i, cond in enumerate(x_conds):

        idx = i + 1

        # x >= 0
        if cond == '>= 0':

            mapping.append([current_idx])

            var_names.append(f"x{idx}")

            c_std.append(c_orig[i])

            current_idx += 1

        # x <= 0
        elif cond == '<= 0':

            mapping.append([current_idx])

            var_names.append(f"x{idx}'")

            c_std.append(-c_orig[i])

            current_idx += 1

        # biến tự do
        elif cond == 'tự do':

            mapping.append(
                [current_idx, current_idx + 1]
            )

            var_names.append(f"x{idx}+")
            var_names.append(f"x{idx}-")

            c_std.append(c_orig[i])
            c_std.append(-c_orig[i])

            current_idx += 2

    n_real = current_idx

    # =====================================================
    # 2. ĐƯA MAX -> MIN
    # =====================================================

    is_max = (
        opt_type.lower() == 'max'
    )

    if is_max:

        c_std = [-v for v in c_std]

    # =====================================================
    # 3. CHUẨN HÓA RÀNG BUỘC
    # =====================================================

    A_std = []

    b_std = []

    for const in constraints:

        row_orig = const['A_row']

        sign = const['sign']

        rhs = const['b']

        real_row = np.zeros(n_real)

        for j, cond in enumerate(x_conds):

            # x >= 0
            if cond == '>= 0':

                real_row[mapping[j][0]] = (
                    row_orig[j]
                )

            # x <= 0
            elif cond == '<= 0':

                real_row[mapping[j][0]] = (
                    -row_orig[j]
                )

            # tự do
            elif cond == 'tự do':

                real_row[mapping[j][0]] = (
                    row_orig[j]
                )

                real_row[mapping[j][1]] = (
                    -row_orig[j]
                )

        # <=
        if sign == '<=':

            A_std.append(real_row)

            b_std.append(rhs)

        # >=
        elif sign == '>=':

            A_std.append(-real_row)

            b_std.append(-rhs)

        # =
        elif sign == '=':

            A_std.append(real_row)

            b_std.append(rhs)

            A_std.append(-real_row)

            b_std.append(-rhs)

    A = np.array(A_std)

    b = np.array(b_std)

    m_real = len(b)

    # =====================================================
    # 4. KIỂM TRA VÔ NGHIỆM
    # =====================================================

    for i in range(m_real):

        if (
            np.all(np.abs(A[i]) < 1e-9)
            and b[i] < -1e-9
        ):

            print("\n" + "="*50)
            print("KẾT LUẬN CUỐI CÙNG:")
            print("Bài toán vô nghiệm.")
            print("="*50 + "\n")

            return

    # =====================================================
    # 5. KIỂM TRA NGHIỆM CƠ SỞ BAN ĐẦU
    # =====================================================

    if np.any(b < -1e-9):

        print("\n[!] Phát hiện b < 0.")
        print("    Cần dùng Simplex 2 Pha hoặc Big-M.")

        return

    # =====================================================
    # 6. KHỞI TẠO TỪ VỰNG
    # =====================================================

    bas_vars = [
        f"w{i+1}"
        for i in range(m_real)
    ]

    non_bas_vars = var_names.copy()

    dict_matrix = np.zeros(
        (m_real + 1,
         n_real + 1)
    )

    # Phần ràng buộc
    dict_matrix[:m_real, :n_real] = -A

    dict_matrix[:m_real, -1] = b

    # Hàm mục tiêu
    dict_matrix[-1, :n_real] = c_std

    dict_matrix[-1, -1] = 0

    # =====================================================
    # HÀM IN TỪ VỰNG
    # =====================================================

    def print_dict():

        print(
            f"\n___ TỪ VỰNG ĐƠN HÌNH "
            f"BƯỚC {step} ___"
        )

        # In hàm mục tiêu
        z_lab = "z'" if is_max else "z"

        z_row = (
            f"{z_lab} = "
            f"{dict_matrix[-1,-1]:.2f}"
        )

        for j in range(len(non_bas_vars)):

            val = dict_matrix[-1, j]

            if abs(val) > 1e-9:

                z_row += (
                    f" {'+' if val > 0 else '-'} "
                    f"{abs(val):.2f}"
                    f"*{non_bas_vars[j]}"
                )

        print(z_row)

        print("-" * 35)

        # In các dòng ràng buộc
        for i in range(m_real):

            row = (
                f"{bas_vars[i]} = "
                f"{dict_matrix[i,-1]:.2f}"
            )

            for j in range(len(non_bas_vars)):

                val = dict_matrix[i, j]

                if abs(val) > 1e-9:

                    row += (
                        f" {'+' if val > 0 else '-'} "
                        f"{abs(val):.2f}"
                        f"*{non_bas_vars[j]}"
                    )

            print(row)

    # =====================================================
    # 7. VÒNG LẶP SIMPLEX
    # =====================================================

    step = 0

    is_unbounded = False

    while True:

        print_dict()

        # ==============================================
        # CHỌN BIẾN VÀO
        # ==============================================

        c_curr = dict_matrix[-1, :-1]

        # tối ưu
        if np.all(c_curr >= -1e-9):

            break

        # hệ số âm nhỏ nhất
        entering_idx = np.argmin(c_curr)

        # ==============================================
        # CHỌN BIẾN RA
        # ==============================================

        ratios = []

        for i in range(m_real):

            coeff = dict_matrix[i, entering_idx]

            if coeff < -1e-9:

                ratios.append(
                    dict_matrix[i, -1]
                    / abs(coeff)
                )

            else:

                ratios.append(np.inf)

        min_ratio = np.min(ratios)

        # Không giới nội
        if min_ratio == np.inf:

            is_unbounded = True

            break

        leaving_row = np.argmin(ratios)

        print(
            f">> Pivot: "
            f"Biến vào = "
            f"{non_bas_vars[entering_idx]} | "
            f"Biến ra = "
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
        ] = 1 / pivot_val

        new_m[
            leaving_row,
            -1
        ] = (
            -dict_matrix[leaving_row, -1]
            / pivot_val
        )

        for j in range(n_real):

            if j != entering_idx:

                new_m[
                    leaving_row,
                    j
                ] = (
                    -dict_matrix[leaving_row, j]
                    / pivot_val
                )

        # Các dòng còn lại
        for i in range(m_real + 1):

            if i != leaving_row:

                mul = dict_matrix[
                    i,
                    entering_idx
                ]

                new_m[i, -1] = (
                    dict_matrix[i, -1]
                    + mul
                    * new_m[leaving_row, -1]
                )

                for j in range(n_real):

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

        # ==============================================
        # ĐỔI BIẾN
        # ==============================================

        bas_vars[leaving_row], non_bas_vars[entering_idx] = (
            non_bas_vars[entering_idx],
            bas_vars[leaving_row]
        )

        dict_matrix = new_m

        step += 1

    # =====================================================
    # 8. KẾT LUẬN
    # =====================================================

    print("\n" + "="*50)
    print("KẾT LUẬN CUỐI CÙNG:")

    # Không giới nội
    if is_unbounded:

        print("Bài toán không giới nội.")

        if is_max:

            print(
                "Giá trị tối ưu: "
                "f_max = +∞"
            )

        else:

            print(
                "Giá trị tối ưu: "
                "f_min = -∞"
            )

        print("="*50 + "\n")

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

    nonbasic_zero = []

    for j in range(len(c_final)):

        if abs(c_final[j]) < 1e-9:

            nonbasic_zero.append(j)

    has_multiple = False

    for j in nonbasic_zero:

        col = dict_matrix[:-1, j]

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
            f"z = {opt_val:.4f}"
        )

    # =====================================================
    # NGHIỆM DUY NHẤT
    # =====================================================

    else:

        print(
            "Bài toán có nghiệm "
            "tối ưu duy nhất:"
        )

        res_vals = {
            v: 0.0
            for v in var_names
        }

        for i, v in enumerate(bas_vars):

            if v in res_vals:

                res_vals[v] = (
                    dict_matrix[i, -1]
                )

        # Khôi phục biến gốc
        for j in range(len(x_conds)):

            idx = j + 1

            # x >= 0
            if x_conds[j] == '>= 0':

                val = res_vals.get(
                    f"x{idx}",
                    0.0
                )

            # x <= 0
            elif x_conds[j] == '<= 0':

                val = -res_vals.get(
                    f"x{idx}'",
                    0.0
                )

            # tự do
            else:

                vp = res_vals.get(
                    f"x{idx}+",
                    0.0
                )

                vn = res_vals.get(
                    f"x{idx}-",
                    0.0
                )

                val = vp - vn

            print(
                f"  x{idx} = {val:.4f}"
            )

        print(
            f"\nGiá trị tối ưu "
            f"{opt_type.capitalize()} "
            f"Z = {opt_val:.4f}"
        )

    print("="*50 + "\n")