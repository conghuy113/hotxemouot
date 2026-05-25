import numpy as np

def in_bang_don_hinh(step, table, row_labels, col_labels):
    """In bảng đơn hình dạng bảng"""

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


def giai_bai_toan_don_hinh_dang_bang(
    opt_type,
    c_orig,
    constraints,
    x_conds
):

    print("\n" + "=" * 50)
    print("GIẢI BÀI TOÁN BẰNG PHƯƠNG PHÁP ĐƠN HÌNH DẠNG BẢNG")
    print("=" * 50)

    # =====================================================
    # 1. CHUẨN HÓA BIẾN
    # =====================================================

    var_names_std = []
    c_std = []

    for i, cond in enumerate(x_conds):

        idx = i + 1

        if cond == '>= 0':

            var_names_std.append(f"x{idx}")
            c_std.append(c_orig[i])

        elif cond == '<= 0':

            var_names_std.append(f"x{idx}'")
            c_std.append(-c_orig[i])

        elif cond == 'tự do':

            var_names_std.append(f"x{idx}+")
            c_std.append(c_orig[i])

            var_names_std.append(f"x{idx}-")
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

            if cond == '>= 0':

                row_std.append(row_orig[i])

            elif cond == '<= 0':

                row_std.append(-row_orig[i])

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

    # =====================================================
    # 3. KIỂM TRA VÔ NGHIỆM
    # =====================================================

    if any(val < -1e-7 for val in b_std):

        print("\nKẾT LUẬN CUỐI CÙNG:")

        print("Bài toán vô nghiệm.")
        print("Miền chấp nhận được rỗng.")

        if is_max:
            print("max z = -inf")
        else:
            print("min z = inf")

        return

    num_constraints = len(b_std)
    num_vars_std = len(c_std)

    # =====================================================
    # 4. KHỞI TẠO BẢNG ĐƠN HÌNH
    # =====================================================

    col_labels = (
        var_names_std
        +
        [f"w{i+1}" for i in range(num_constraints)]
    )

    row_labels = (
        [f"w{i+1}" for i in range(num_constraints)]
        +
        ["-z"]
    )

    total_cols = len(col_labels) + 1
    total_rows = len(row_labels)

    table = np.zeros((total_rows, total_cols))

    # các ràng buộc
    for i in range(num_constraints):

        table[i, :num_vars_std] = A_std[i]

        table[i, num_vars_std + i] = 1.0

        table[i, -1] = b_std[i]

    # dòng z
    table[-1, :num_vars_std] = c_std

    step = 0

    in_bang_don_hinh(
        step,
        table,
        row_labels,
        col_labels
    )

    # =====================================================
    # 5. SIMPLEX TABLEAU
    # =====================================================

    is_unbounded = False

    while True:

        z_row = table[-1, :-1]

        # tối ưu
        if np.all(z_row >= -1e-9):
            break

        # biến vào
        pivot_col = np.argmin(z_row)

        # ratio test
        ratios = []
        valid_rows = []

        for i in range(num_constraints):

            coeff = table[i, pivot_col]

            if coeff > 1e-9:

                ratio = table[i, -1] / coeff

                ratios.append(ratio)

                valid_rows.append(i)

        # không giới nội
        if not ratios:

            is_unbounded = True
            break

        min_ratio_idx = np.argmin(ratios)

        pivot_row = valid_rows[min_ratio_idx]

        print(
            f">> Khớp xoay: "
            f"Biến vào {col_labels[pivot_col]} | "
            f"Biến ra {row_labels[pivot_row]}"
        )

        # đổi biến cơ sở
        row_labels[pivot_row] = col_labels[pivot_col]

        # pivot
        pivot_element = table[pivot_row, pivot_col]

        new_table = np.zeros_like(table)

        # dòng trục
        new_table[pivot_row, :] = (
            table[pivot_row, :]
            / pivot_element
        )

        # khử Gauss
        for i in range(total_rows):

            if i != pivot_row:

                factor = table[i, pivot_col]

                new_table[i, :] = (
                    table[i, :]
                    -
                    factor * new_table[pivot_row, :]
                )

        table = new_table

        step += 1

        in_bang_don_hinh(
            step,
            table,
            row_labels,
            col_labels
        )

    # =====================================================
    # 6. KẾT LUẬN
    # =====================================================

    print("\n" + "=" * 50)
    print("KẾT LUẬN CUỐI CÙNG:")

    # -----------------------------------------------------
    # TH1: KHÔNG GIỚI NỘI
    # -----------------------------------------------------

    if is_unbounded:

        print("Bài toán không giới nội.")

        if is_max:
            print("max z = inf")
        else:
            print("min z = -inf")

        print("=" * 50 + "\n")

        return

    # -----------------------------------------------------
    # TH2: VÔ SỐ NGHIỆM
    # -----------------------------------------------------

    z_row = table[-1, :-1]

    basic_vars = row_labels[:-1]

    has_multiple = False

    for j, val in enumerate(z_row):

        var = col_labels[j]

        if (
            abs(val) < 1e-7
            and var not in basic_vars
        ):
            has_multiple = True
            break

    # -----------------------------------------------------
    # TRÍCH XUẤT NGHIỆM
    # -----------------------------------------------------

    sol_std = {

        v: 0.0
        for v in var_names_std

    }

    for i, label in enumerate(row_labels[:-1]):

        if label in sol_std:

            sol_std[label] = table[i, -1]

    # -----------------------------------------------------
    # GIÁ TRỊ TỐI ƯU
    # -----------------------------------------------------

    res_z = -table[-1, -1]

    if is_max:
        res_z = -res_z

    # -----------------------------------------------------
    # IN KẾT LUẬN
    # -----------------------------------------------------

    if has_multiple:

        print("Bài toán có vô số nghiệm tối ưu.")

    else:

        print("Bài toán có nghiệm tối ưu duy nhất.")

    print("\nNghiệm của các biến gốc ban đầu:")

    for i, cond in enumerate(x_conds):

        idx = i + 1

        val = 0.0

        if cond == '>= 0':

            val = sol_std[f"x{idx}"]

        elif cond == '<= 0':

            val = -sol_std[f"x{idx}'"]

        elif cond == 'tự do':

            val = (
                sol_std[f"x{idx}+"]
                -
                sol_std[f"x{idx}-"]
            )

        print(f"  x{idx} = {val:.4f}")

    print(
        f"\nGiá trị tối ưu "
        f"{opt_type.capitalize()} Z = {res_z:.4f}"
    )

    print("=" * 50 + "\n")