import numpy as np
import matplotlib.pyplot as plt
import math
from itertools import combinations
from scipy.optimize import linprog


def get_lcm(a, b):
    """Tìm BCNN phục vụ vẽ hướng hàm mục tiêu"""

    if a == 0 or b == 0:
        return max(abs(a), abs(b), 1)

    scale = 100

    ia = int(abs(a) * scale)
    ib = int(abs(b) * scale)

    gcd = math.gcd(ia, ib)

    return (ia * ib) / gcd / scale


def tim_cac_dinh(constraints, bounds):
    """
    Tìm tất cả các đỉnh của miền chấp nhận
    """

    lines = []

    # Chuyển về dạng ax + by = c
    for const in constraints:

        a, b = const['A_row']
        c = const['b']

        lines.append((a, b, c))

    # Bound x1
    if bounds[0][0] is not None:
        lines.append((1, 0, bounds[0][0]))

    if bounds[0][1] is not None:
        lines.append((1, 0, bounds[0][1]))

    # Bound x2
    if bounds[1][0] is not None:
        lines.append((0, 1, bounds[1][0]))

    if bounds[1][1] is not None:
        lines.append((0, 1, bounds[1][1]))

    vertices = []

    # Giao từng cặp đường
    for l1, l2 in combinations(lines, 2):

        a1, b1, c1 = l1
        a2, b2, c2 = l2

        det = a1 * b2 - a2 * b1

        # Song song
        if abs(det) < 1e-9:
            continue

        x = (c1 * b2 - c2 * b1) / det
        y = (a1 * c2 - a2 * c1) / det

        ok = True

        # =========================
        # Kiểm tra bounds
        # =========================

        if bounds[0][0] is not None:
            if x < bounds[0][0] - 1e-7:
                ok = False

        if bounds[0][1] is not None:
            if x > bounds[0][1] + 1e-7:
                ok = False

        if bounds[1][0] is not None:
            if y < bounds[1][0] - 1e-7:
                ok = False

        if bounds[1][1] is not None:
            if y > bounds[1][1] + 1e-7:
                ok = False

        # =========================
        # Kiểm tra ràng buộc
        # =========================

        for const in constraints:

            a, b = const['A_row']
            rhs = const['b']
            sign = const['sign']

            val = a * x + b * y

            if sign == "<=":

                if val > rhs + 1e-7:
                    ok = False

            elif sign == ">=":

                if val < rhs - 1e-7:
                    ok = False

            elif sign == "=":

                if abs(val - rhs) > 1e-7:
                    ok = False

        if ok:
            vertices.append((round(x, 8), round(y, 8)))

    # Loại trùng
    vertices = list(set(vertices))

    return vertices


def giai_bai_toan_truot_ham_muc_tieu(
    opt_type,
    c_orig,
    constraints,
    x_conds,
    show_plot=True,
    return_fig=False):

    print("\n" + "=" * 50)
    print("GIẢI BÀI TOÁN BẰNG PHƯƠNG PHÁP ĐỒ THỊ")
    print("=" * 50)

    n_vars = len(c_orig)

    # scipy luôn giải Min
    c_for_scipy = (
        [-v for v in c_orig]
        if opt_type.lower() == "max"
        else c_orig
    )

    # ==========================================
    # Phân loại ràng buộc
    # ==========================================

    A_ub = []
    b_ub = []

    A_eq = []
    b_eq = []

    for const in constraints:

        row = const['A_row']
        sign = const['sign']
        rhs = const['b']

        if sign == "=":

            A_eq.append(row)
            b_eq.append(rhs)

        elif sign == "<=":

            A_ub.append(row)
            b_ub.append(rhs)

        elif sign == ">=":

            A_ub.append([-v for v in row])
            b_ub.append(-rhs)

    # ==========================================
    # Bounds
    # ==========================================

    bounds = []

    for cond in x_conds:

        if cond == ">= 0":

            bounds.append((0, None))

        elif cond == "<= 0":

            bounds.append((None, 0))

        elif cond == "tự do":

            bounds.append((None, None))

        else:

            bounds.append((0, None))

    # ==========================================
    # Giải bằng scipy
    # ==========================================

    res = linprog(
        c_for_scipy,
        A_ub=A_ub if A_ub else None,
        b_ub=b_ub if b_ub else None,
        A_eq=A_eq if A_eq else None,
        b_eq=b_eq if b_eq else None,
        bounds=bounds,
        method='highs'
    )

    # ==========================================
    # In kết quả
    # ==========================================

    print("\n" + "-" * 50)

    # ==========================================
    # Có nghiệm tối ưu
    # ==========================================

    if res.status == 0:

        val_toi_uu = (
            -res.fun
            if opt_type.lower() == "max"
            else res.fun
        )

        # ==========================================
        # Kiểm tra vô số nghiệm tối ưu
        # ==========================================

        vertices = tim_cac_dinh(
            constraints,
            bounds
        )

        optimal_vertices = []

        for v in vertices:

            z = (
                c_orig[0] * v[0]
                + c_orig[1] * v[1]
            )

            if abs(z - val_toi_uu) < 1e-6:
                optimal_vertices.append(v)

        # ==========================================
        # Vô số nghiệm tối ưu
        # ==========================================

        if len(optimal_vertices) >= 2:

            A = optimal_vertices[0]
            B = optimal_vertices[1]

            print(
                "KẾT QUẢ: "
                "BÀI TOÁN CÓ VÔ SỐ NGHIỆM TỐI ƯU\n"
            )

            print(
                "Tập nghiệm tối ưu là đoạn thẳng nối:"
            )

            print(
                f"A({A[0]:.4f}, {A[1]:.4f})"
            )

            print(
                f"B({B[0]:.4f}, {B[1]:.4f})"
            )

            print("\nGiá trị tối ưu duy nhất:")

            print(
                f"{opt_type.upper()} "
                f"Z = {val_toi_uu:.4f}"
            )

        # ==========================================
        # Nghiệm tối ưu duy nhất
        # ==========================================

        else:

            print(
                "KẾT QUẢ: "
                "BÀI TOÁN CÓ NGHIỆM TỐI ƯU DUY NHẤT\n"
            )

            print(
                f"{opt_type.upper()} "
                f"Z = {val_toi_uu:.4f}"
            )

            for i in range(n_vars):

                print(
                    f"x{i+1} = {res.x[i]:.4f}"
                )

    # ==========================================
    # Vô nghiệm
    # ==========================================

    elif res.status == 2:

        print(
            "KẾT QUẢ: "
            "BÀI TOÁN VÔ NGHIỆM"
        )

        if opt_type.lower() == "max":
            print("max Z = -inf")
        else:
            print("min Z = inf")

    # ==========================================
    # Không giới nội
    # ==========================================

    elif res.status == 3:

        print(
            "KẾT QUẢ: "
            "BÀI TOÁN KHÔNG GIỚI NỘI"
        )

        if opt_type.lower() == "max":
            print("max Z = inf")
        else:
            print("min Z = -inf")

    # ==========================================
    # Lỗi khác
    # ==========================================

    else:

        print(
            f"KẾT QUẢ: "
            f"Không thể giải. "
            f"Lỗi: {res.message}"
        )

    print("-" * 50)

    # ==========================================
    # Vẽ hình
    # ==========================================

    if n_vars == 2:

        fig = ve_hinh_2d(
            c_orig,
            constraints,
            res,
            opt_type,
            bounds,
            show_plot=show_plot,
            return_fig=return_fig
        )

        if return_fig:
            return fig

    else:

        print(
            f"\n[!] Bài toán có {n_vars} biến. "
            "Phương pháp đồ thị "
            "chỉ hỗ trợ không gian 2D."
        )


def ve_hinh_2d(
    c_coeffs,
    constraints,
    res,
    opt_type,
    bounds,
    show_plot=True,
    return_fig=False):

    """
    Vẽ miền nghiệm và đường mục tiêu
    """

    # ==========================================
    # Phạm vi vẽ
    # ==========================================

    max_v = 15.0

    if res.status == 0 and res.x is not None:

        max_v = max(
            max(np.abs(res.x)),
            10.0
        ) * 1.5

    d = np.linspace(-max_v, max_v, 600)

    X, Y = np.meshgrid(d, d)

    fig = plt.figure(figsize=(10, 8))

    # ==========================================
    # Miền nghiệm
    # ==========================================

    feasible_mask = np.ones_like(
        X,
        dtype=bool
    )

    # Bounds
    if bounds[0][0] is not None:
        feasible_mask &= (X >= bounds[0][0])

    if bounds[0][1] is not None:
        feasible_mask &= (X <= bounds[0][1])

    if bounds[1][0] is not None:
        feasible_mask &= (Y >= bounds[1][0])

    if bounds[1][1] is not None:
        feasible_mask &= (Y <= bounds[1][1])

    # Constraints
    for const in constraints:

        row = const['A_row']
        sign = const['sign']
        rhs = const['b']

        expr = row[0] * X + row[1] * Y

        if sign == "<=":

            feasible_mask &= (
                expr <= rhs + 1e-7
            )

        elif sign == ">=":

            feasible_mask &= (
                expr >= rhs - 1e-7
            )

        elif sign == "=":

            feasible_mask &= (
                np.abs(expr - rhs) < 0.05
            )

    # Tô màu
    if np.any(feasible_mask):

        plt.imshow(
            feasible_mask.astype(int),
            extent=(
                -max_v,
                max_v,
                -max_v,
                max_v
            ),
            origin="lower",
            cmap="Greens",
            alpha=0.3
        )

    # ==========================================
    # Vẽ ràng buộc
    # ==========================================

    for i, const in enumerate(constraints):

        row = const['A_row']
        sign = const['sign']
        rhs = const['b']

        label = (
            f"RB{i+1}: "
            f"{row[0]}x1 + "
            f"{row[1]}x2 "
            f"{sign} {rhs}"
        )

        # Không thẳng đứng
        if abs(row[1]) > 1e-9:

            y_vals = (
                rhs - row[0] * d
            ) / row[1]

            plt.plot(
                d,
                y_vals,
                label=label
            )

        # Thẳng đứng
        else:

            if abs(row[0]) > 1e-9:

                x_const = rhs / row[0]

                plt.axvline(
                    x=x_const,
                    label=label
                )

    # ==========================================
    # Hướng hàm mục tiêu
    # ==========================================

    try:

        lcm_val = get_lcm(
            c_coeffs[0],
            c_coeffs[1]
        )

        if abs(c_coeffs[1]) > 1e-9:

            y_obj = (
                lcm_val
                - c_coeffs[0] * d
            ) / c_coeffs[1]

            plt.plot(
                d,
                y_obj,
                'b:',
                linewidth=1.5,
                alpha=0.6,
                label='Hướng song song của Z'
            )

    except:
        pass

    # ==========================================
    # Nghiệm tối ưu
    # ==========================================

    if res.status == 0 and res.x is not None:

        opt_val = (
            c_coeffs[0] * res.x[0]
            + c_coeffs[1] * res.x[1]
        )

        # Đường tối ưu
        if abs(c_coeffs[1]) > 1e-9:

            y_opt = (
                opt_val
                - c_coeffs[0] * d
            ) / c_coeffs[1]

            plt.plot(
                d,
                y_opt,
                'r-',
                linewidth=2,
                label=f'Đường tối ưu Z={opt_val:.2f}'
            )

        else:

            if abs(c_coeffs[0]) > 1e-9:

                plt.axvline(
                    x=opt_val / c_coeffs[0],
                    color='r',
                    linewidth=2,
                    label=f'Đường tối ưu Z={opt_val:.2f}'
                )

        # ==========================================
        # Kiểm tra vô số nghiệm
        # ==========================================

        vertices = tim_cac_dinh(
            constraints,
            bounds
        )

        optimal_vertices = []

        for v in vertices:

            z = (
                c_coeffs[0] * v[0]
                + c_coeffs[1] * v[1]
            )

            if abs(z - opt_val) < 1e-6:
                optimal_vertices.append(v)

        # ==========================================
        # Vô số nghiệm tối ưu
        # ==========================================

        if len(optimal_vertices) >= 2:

            A = optimal_vertices[0]
            B = optimal_vertices[1]

            plt.plot(
                [A[0], B[0]],
                [A[1], B[1]],
                'r',
                linewidth=4,
                label='Đoạn nghiệm tối ưu'
            )

            plt.plot(A[0], A[1], 'ko')
            plt.plot(B[0], B[1], 'ko')

            plt.annotate(
                f"A({A[0]:.2f},{A[1]:.2f})",
                A,
                xytext=(5, 5),
                textcoords='offset points'
            )

            plt.annotate(
                f"B({B[0]:.2f},{B[1]:.2f})",
                B,
                xytext=(5, 5),
                textcoords='offset points'
            )

        # ==========================================
        # Nghiệm duy nhất
        # ==========================================

        else:

            plt.plot(
                res.x[0],
                res.x[1],
                'ro',
                markersize=8,
                label='Nghiệm tối ưu'
            )

            plt.annotate(
                f"({res.x[0]:.2f}, "
                f"{res.x[1]:.2f})",
                (res.x[0], res.x[1]),
                xytext=(10, 10),
                textcoords='offset points',
                color='red',
                weight='bold'
            )

    # ==========================================
    # Thiết lập đồ thị
    # ==========================================

    plt.title(
        f"Phương pháp Đồ thị "
        f"({opt_type.capitalize()} Z)\n"
        f"Trạng thái: {res.message}"
    )

    if res.status == 0 and res.x is not None:

        plt.xlim(
            res.x[0] - max_v / 1.5,
            res.x[0] + max_v / 1.5
        )

        plt.ylim(
            res.x[1] - max_v / 1.5,
            res.x[1] + max_v / 1.5
        )

    else:

        plt.xlim(-15, 15)
        plt.ylim(-15, 15)

    plt.xlabel('x1')
    plt.ylabel('x2')

    plt.axhline(0, color='black', lw=1)
    plt.axvline(0, color='black', lw=1)

    plt.legend(
        loc='upper right',
        fontsize='small'
    )

    plt.grid(True, alpha=0.3)

    if show_plot:
        plt.show()
    else:
        plt.close(fig)

    if return_fig:
        return fig