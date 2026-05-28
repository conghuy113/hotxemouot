import math

from utils import (
    var_sort_key,
    in_tu_vung,
    pivot
)


def giai_bai_toan_don_hinh(
    opt_type,
    c_orig,
    constraints,
    x_conds
):

    print("\n" + "=" * 60)
    print("THUẬT TOÁN ĐƠN HÌNH 2 PHA")
    print("=" * 60)

    # =====================================================
    # 1. CHUẨN HÓA BIẾN
    # =====================================================

    var_names = []

    c_std = []

    for i, cond in enumerate(x_conds):

        idx = i + 1

        # x >= 0
        if cond == ">= 0":

            var_names.append(f"x{idx}")

            c_std.append(c_orig[i])

        # x <= 0
        elif cond == "<= 0":

            var_names.append(f"x{idx}'")

            c_std.append(-c_orig[i])

        # biến tự do
        elif cond == "tự do":

            var_names.append(f"x{idx}+")
            c_std.append(c_orig[i])

            var_names.append(f"x{idx}-")
            c_std.append(-c_orig[i])

    # =====================================================
    # MAX -> MIN
    # =====================================================

    is_max = opt_type.lower() == "max"

    if is_max:

        c_std = [-v for v in c_std]

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
            if cond == ">= 0":

                row_std.append(row_orig[i])

            # x <= 0
            elif cond == "<= 0":

                row_std.append(-row_orig[i])

            # tự do
            elif cond == "tự do":

                row_std.append(row_orig[i])

                row_std.append(-row_orig[i])

        # =========================================
        # ĐƯA VỀ <=
        # =========================================

        if sign == ">=":

            row_std = [-v for v in row_std]

            rhs = -rhs

        elif sign == "=":

            A_std.append(row_std)
            b_std.append(rhs)

            A_std.append([-v for v in row_std])
            b_std.append(-rhs)

            continue

        A_std.append(row_std)

        b_std.append(rhs)

    # =====================================================
    # 3. KIỂM TRA VÔ NGHIỆM HIỂN NHIÊN
    # =====================================================

    for i in range(len(b_std)):

        row = A_std[i]

        if all(abs(v) < 1e-9 for v in row) and b_std[i] < -1e-9:

            print("\nBÀI TOÁN VÔ NGHIỆM")

            if is_max:
                print("max z = -inf")
            else:
                print("min z = inf")

            return

    # =====================================================
    # 4. KHỞI TẠO TỪ VỰNG
    # =====================================================

    num_constraints = len(b_std)

    basis = [

        f"w{i+1}"
        for i in range(num_constraints)

    ]

    non_basis = list(var_names)

    dict_b = {

        basis[i]: b_std[i]
        for i in range(num_constraints)

    }

    dict_A = {}

    for i in range(num_constraints):

        dict_A[basis[i]] = {}

        for j, var in enumerate(non_basis):

            dict_A[basis[i]][var] = -A_std[i][j]

    # =====================================================
    # 5. HÀM MỤC TIÊU
    # =====================================================

    Z_v = 0.0

    Z_C = {

        non_basis[j]: c_std[j]
        for j in range(len(non_basis))

    }

    step = 0

    # =====================================================
    # 6. KIỂM TRA b_i < 0
    # =====================================================

    needs_phase_1 = any(

        b < -1e-7
        for b in dict_b.values()

    )

    # =====================================================
    # 7. PHA 1
    # =====================================================

    if needs_phase_1:

        print("\nPHÁT HIỆN TỒN TẠI b_i < 0")
        print("BẮT ĐẦU PHA 1\n")

        # -------------------------------------------------
        # THÊM x0
        # -------------------------------------------------

        non_basis.append("x0")

        for b_var in basis:

            dict_A[b_var]["x0"] = 1.0

        # -------------------------------------------------
        # epsilon = x0
        # -------------------------------------------------

        W_v = 0.0

        W_C = {

            var: 0.0
            for var in non_basis

        }

        W_C["x0"] = 1.0

        # -------------------------------------------------
        # IN BÀI TOÁN PHA 1
        # -------------------------------------------------

        print("Pha 1:\n")

        print("Bài toán bổ trợ (BT'):")

        print("{")

        print("   min ε = x0")

        for i, b_var in enumerate(basis):

            expr = ""

            first = True

            for var in non_basis:

                coeff = -dict_A[b_var][var]

                if abs(coeff) < 1e-9:
                    continue

                if first:

                    if coeff < 0:
                        expr += f"- {abs(coeff):.2f}{var}"
                    else:
                        expr += f"{coeff:.2f}{var}"

                    first = False

                else:

                    if coeff >= 0:
                        expr += f" + {coeff:.2f}{var}"
                    else:
                        expr += f" - {abs(coeff):.2f}{var}"

            print(f"   {expr} <= {dict_b[b_var]:.2f}")

        all_vars = ", ".join(non_basis)

        print(f"   {all_vars} >= 0")

        print("}\n")

        # -------------------------------------------------
        # IN TỪ VỰNG XUẤT PHÁT
        # -------------------------------------------------

        print("Từ vựng xuất phát:\n")

        print("ε = x0\n")

        for b_var in basis:

            expr = f"{b_var} = {dict_b[b_var]:.2f}"

            for var in non_basis:

                coeff = dict_A[b_var][var]

                if abs(coeff) < 1e-9:
                    continue

                if coeff > 0:
                    expr += f" + {coeff:.2f}*{var}"
                else:
                    expr += f" - {abs(coeff):.2f}*{var}"

            print(expr)

        print()

        # -------------------------------------------------
        # PIVOT ĐẦU TIÊN
        # -------------------------------------------------

        leaving_var = min(

            basis,
            key=lambda v: (
                dict_b[v],
                var_sort_key(v)
            )

        )

        entering_var = "x0"

        print(f"Biến vào : {entering_var}")
        print(f"Biến ra  : {leaving_var}")

        basis, non_basis, dict_b, dict_A, W_v, W_C, Z_v, Z_C = pivot(

            basis,
            non_basis,
            dict_b,
            dict_A,
            W_v,
            W_C,
            Z_v,
            Z_C,
            entering_var,
            leaving_var

        )

        step += 1

        # =================================================
        # SIMPLEX PHA 1
        # =================================================

        while True:

            in_tu_vung(

                step,
                basis,
                non_basis,
                dict_b,
                dict_A,
                W_v,
                W_C,
                "ε"

            )

            negative_vars = {

                v: coeff
                for v, coeff in W_C.items()
                if coeff < -1e-7

            }

            if not negative_vars:

                break

            min_coeff = min(
                negative_vars.values()
            )

            candidates_in = [

                v
                for v, coeff in negative_vars.items()
                if abs(coeff - min_coeff) < 1e-7

            ]

            entering_var = sorted(
                candidates_in,
                key=var_sort_key
            )[0]

            candidates_out = []

            for b_var in basis:

                coeff = dict_A[b_var][entering_var]

                if coeff < -1e-7:

                    ratio = (

                        dict_b[b_var]
                        / abs(coeff)

                    )

                    candidates_out.append(
                        (ratio, b_var)
                    )

            if not candidates_out:

                print("\nBài toán bổ trợ không giới nội")

                return

            min_ratio = min(
                candidates_out,
                key=lambda x: x[0]
            )[0]

            best_out = [

                b_var
                for r, b_var in candidates_out
                if abs(r - min_ratio) < 1e-7

            ]

            leaving_var = sorted(
                best_out,
                key=var_sort_key
            )[0]

            print(f"\nBiến vào : {entering_var}")
            print(f"Biến ra  : {leaving_var}")

            basis, non_basis, dict_b, dict_A, W_v, W_C, Z_v, Z_C = pivot(

                basis,
                non_basis,
                dict_b,
                dict_A,
                W_v,
                W_C,
                Z_v,
                Z_C,
                entering_var,
                leaving_var

            )

            step += 1

        # =================================================
        # KẾT THÚC PHA 1
        # =================================================

        print("\nKẾT THÚC PHA 1")

        # -------------------------------------------------
        # TH2: VÔ NGHIỆM
        # -------------------------------------------------

        if abs(W_v) > 1e-7:

            print("\nTH2:")
            print("x0 != 0")

            print("=> miền chấp nhận được rỗng")
            print("=> bài toán vô nghiệm")

            if is_max:

                print("max z = -inf")

            else:

                print("min z = inf")

            return

        # -------------------------------------------------
        # TH1: CÓ MIỀN CHẤP NHẬN
        # -------------------------------------------------

        else:

            print("\nTH1:")
            print("x0 = 0")

            print("=> chọn x0 = 0")

            print("=> miền chấp nhận được khác rỗng")

            print("=> hệ ràng buộc trở thành:")

            for b_var in basis:

                if b_var == "x0":
                    continue

                expr = f"{b_var} = {dict_b[b_var]:.2f}"

                for var in non_basis:

                    if var == "x0":
                        continue

                    coeff = dict_A[b_var][var]

                    if abs(coeff) < 1e-9:
                        continue

                    if coeff > 0:

                        expr += f" + {coeff:.2f}*{var}"

                    else:

                        expr += f" - {abs(coeff):.2f}*{var}"

                print(expr)

            print("\n=> chuyển sang pha 2")

        # =================================================
        # XÓA x0
        # =================================================

        if "x0" in basis:

            row = "x0"

            for var in non_basis:

                if var != "x0":

                    if abs(dict_A[row][var]) > 1e-7:

                        basis, non_basis, dict_b, dict_A, W_v, W_C, Z_v, Z_C = pivot(

                            basis,
                            non_basis,
                            dict_b,
                            dict_A,
                            W_v,
                            W_C,
                            Z_v,
                            Z_C,
                            var,
                            row

                        )

                        break

        if "x0" in non_basis:

            non_basis.remove("x0")

        for b_var in basis:

            if "x0" in dict_A[b_var]:

                del dict_A[b_var]["x0"]

        if "x0" in Z_C:

            del Z_C["x0"]

    else:

        print("\nMọi b_i >= 0")
        print("Không cần pha 1")

    # =====================================================
    # 8. PHA 2
    # =====================================================

    print("\nBẮT ĐẦU PHA 2\n")

    is_unbounded = False

    while True:

        in_tu_vung(

            step,
            basis,
            non_basis,
            dict_b,
            dict_A,
            Z_v,
            Z_C,
            "z"

        )

        negative_vars = {

            v: coeff
            for v, coeff in Z_C.items()
            if coeff < -1e-7

        }

        if not negative_vars:

            print("\nĐÃ TỐI ƯU")

            break

        min_coeff = min(
            negative_vars.values()
        )

        candidates_in = [

            v
            for v, coeff in negative_vars.items()
            if abs(coeff - min_coeff) < 1e-7

        ]

        entering_var = sorted(
            candidates_in,
            key=var_sort_key
        )[0]

        candidates_out = []

        for b_var in basis:

            coeff = dict_A[b_var][entering_var]

            if coeff < -1e-7:

                ratio = (

                    dict_b[b_var]
                    / abs(coeff)

                )

                candidates_out.append(
                    (ratio, b_var)
                )

        if not candidates_out:

            is_unbounded = True

            break

        min_ratio = min(
            candidates_out,
            key=lambda x: x[0]
        )[0]

        best_out = [

            b_var
            for r, b_var in candidates_out
            if abs(r - min_ratio) < 1e-7

        ]

        leaving_var = sorted(
            best_out,
            key=var_sort_key
        )[0]

        print(f"\nBiến vào : {entering_var}")
        print(f"Biến ra  : {leaving_var}")

        basis, non_basis, dict_b, dict_A, _, _, Z_v, Z_C = pivot(

            basis,
            non_basis,
            dict_b,
            dict_A,
            0,
            None,
            Z_v,
            Z_C,
            entering_var,
            leaving_var

        )

        step += 1

    # =====================================================
    # 9. KẾT LUẬN
    # =====================================================

    print("\n" + "=" * 60)
    print("KẾT LUẬN CUỐI CÙNG")
    print("=" * 60)

    # =====================================================
    # KHÔNG GIỚI NỘI
    # =====================================================

    if is_unbounded:

        print("\nBài toán không giới nội.")

        if is_max:
            print("max z = inf")
        else:
            print("min z = -inf")

        return

    # =====================================================
    # GIÁ TRỊ TỐI ƯU
    # =====================================================

    final_z = -Z_v if is_max else Z_v

    # =====================================================
    # VÔ SỐ NGHIỆM
    # =====================================================

    has_multiple = False

    for nb_var in non_basis:

        if abs(Z_C.get(nb_var, 0.0)) < 1e-7:

            for b_var in basis:

                coeff = dict_A[b_var][nb_var]

                if coeff < -1e-7:

                    has_multiple = True
                    break

        if has_multiple:
            break

    if has_multiple:

        print("\nBài toán có vô số nghiệm tối ưu.")

        print(
            f"Giá trị tối ưu "
            f"{opt_type} z = {final_z:.4f}"
        )

        return

    # =====================================================
    # NGHIỆM DUY NHẤT
    # =====================================================

    print("\nBài toán có nghiệm tối ưu duy nhất:")

    res = {

        var: 0.0
        for var in var_names

    }

    for b_var in basis:

        if b_var in res:

            res[b_var] = dict_b[b_var]

    # khôi phục biến gốc
    for i, cond in enumerate(x_conds):

        idx = i + 1

        val = 0.0

        if cond == ">= 0":

            val = res.get(
                f"x{idx}",
                0.0
            )

        elif cond == "<= 0":

            val = -res.get(
                f"x{idx}'",
                0.0
            )

        elif cond == "tự do":

            val = (

                res.get(f"x{idx}+", 0.0)

                -

                res.get(f"x{idx}-", 0.0)

            )

        print(f"x{idx} = {val:.4f}")

    print(
        f"\nGiá trị tối ưu "
        f"{opt_type} z = {final_z:.4f}"
    )

    print("=" * 60)