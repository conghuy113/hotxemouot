import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull

EPS = 1e-9


def giai_bai_toan_hinh_hoc_2_rb(
    opt_type,
    c_orig,
    constraints,
    x_conds,
    show_plot=True,
    return_fig=False,
):
    """
    GIẢI BÀI TOÁN QUY HOẠCH TUYẾN TÍNH
    BẰNG PHƯƠNG PHÁP BAO LỒI VECTƠ

    Hỗ trợ:
    - Min / Max
    - Biến >=0
    - Biến <=0
    - Biến tự do
    - Ràng buộc <=, >=, =
    - Có nghiệm duy nhất
    - Vô số nghiệm
    - Vô nghiệm
    - Không giới nội
    """

    print("\n" + "=" * 70)
    print("GIẢI BÀI TOÁN BẰNG PHƯƠNG PHÁP BAO LỒI VECTƠ")
    print("=" * 70)

    # =========================================================
    # 0. KIỂM TRA
    # =========================================================

    if len(constraints) != 2:
        print("[!] Phương pháp này yêu cầu đúng 2 ràng buộc.")
        return

    # =========================================================
    # 1. CHUYỂN BIẾN VỀ >= 0
    # =========================================================

    c_std = []
    A_std = [[], []]

    var_labels = []
    mapping = []

    current_idx = 0

    for i, cond in enumerate(x_conds):

        a1 = constraints[0]["A_row"][i]
        a2 = constraints[1]["A_row"][i]
        c = c_orig[i]

        # x >= 0
        if cond == ">= 0":

            c_std.append(c)

            A_std[0].append(a1)
            A_std[1].append(a2)

            var_labels.append(f"x{i+1}")

            mapping.append(("normal", current_idx))

            current_idx += 1

        # x <= 0
        elif cond == "<= 0":

            c_std.append(-c)

            A_std[0].append(-a1)
            A_std[1].append(-a2)

            var_labels.append(f"x{i+1}'")

            mapping.append(("negative", current_idx))

            current_idx += 1

        # biến tự do
        elif cond == "tự do":

            # x+
            c_std.append(c)

            A_std[0].append(a1)
            A_std[1].append(a2)

            var_labels.append(f"x{i+1}+")

            plus_idx = current_idx

            current_idx += 1

            # x-
            c_std.append(-c)

            A_std[0].append(-a1)
            A_std[1].append(-a2)

            var_labels.append(f"x{i+1}-")

            minus_idx = current_idx

            current_idx += 1

            mapping.append(("free", plus_idx, minus_idx))

    A_std = np.array(A_std, dtype=float)
    c_std = np.array(c_std, dtype=float)

    # =========================================================
    # 2. MAX -> MIN
    # =========================================================

    is_max = opt_type.lower() == "max"

    if is_max:
        c_std = -c_std

    # =========================================================
    # 3. CHUẨN HÓA RÀNG BUỘC <=
    # =========================================================

    signs = [
        constraints[0]["sign"],
        constraints[1]["sign"]
    ]

    b_std = np.array([
        constraints[0]["b"],
        constraints[1]["b"]
    ], dtype=float)

    for r in range(2):

        if signs[r] == ">=":

            A_std[r] = -A_std[r]
            b_std[r] = -b_std[r]

            signs[r] = "<="

        if b_std[r] < 0:

            A_std[r] = -A_std[r]
            b_std[r] = -b_std[r]

    # =========================================================
    # 4. THÊM BIẾN PHỤ
    # =========================================================

    slack_count = 0

    for s in signs:
        if s != "=":
            slack_count += 1

    total_vars = len(c_std) + slack_count

    A_full = np.zeros((2, total_vars))

    A_full[:, :len(c_std)] = A_std

    c_full = list(c_std)

    slack_idx = len(c_std)

    for r in range(2):

        if signs[r] == "<=":

            A_full[r, slack_idx] = 1.0

            c_full.append(0.0)

            var_labels.append(f"w{r+1}")

            slack_idx += 1

    c_full = np.array(c_full)

    # =========================================================
    # 5. PHƯƠNG TRÌNH TỔ HỢP
    # =========================================================

    print("\n___ PHƯƠNG TRÌNH TỔ HỢP LỒI ___")

    h = A_full[0] + A_full[1]

    K = b_std[0] + b_std[1]

    if K < 0:
        h = -h
        K = -K

    expr = " + ".join([
        f"({h[j]:.2f})*{var_labels[j]}"
        for j in range(total_vars)
    ])

    print(f"{expr} = {K:.4f}")

    # =========================================================
    # 6. TỌA ĐỘ CÁC ĐIỂM
    # =========================================================

    multipliers = []

    for j in range(total_vars):

        if abs(h[j]) < EPS:
            multipliers.append(np.inf)
        else:
            multipliers.append(K / h[j])

    points = []
    valid_idx = []

    print("\n___ TỌA ĐỘ CÁC ĐIỂM ___")

    for j in range(total_vars):

        mult = multipliers[j]

        if not np.isfinite(mult):

            points.append((np.nan, np.nan))

            print(f"a_{j+1} = Không xác định")

            continue

        x_coord = A_full[1, j] * mult
        y_coord = c_full[j] * mult

        points.append((x_coord, y_coord))

        valid_idx.append(j)

        print(
            f"a_{j+1} ({var_labels[j]}) = "
            f"({x_coord:.4f}, {y_coord:.4f})"
        )

    # =========================================================
    # 7. QUÉT NGHIỆM
    # =========================================================

    target_x = b_std[1]

    print(f"\nĐường quét: x = {target_x:.4f}")

    intersections = []

    for i in valid_idx:

        for j in valid_idx:

            if i >= j:
                continue

            x1, y1 = points[i]
            x2, y2 = points[j]

            # đường quét cắt đoạn
            if (
                min(x1, x2) - EPS
                <= target_x
                <= max(x1, x2) + EPS
            ):

                M = np.array([
                    [1.0, 1.0],
                    [x1, x2]
                ])

                B = np.array([
                    1.0,
                    target_x
                ])

                try:

                    lambdas = np.linalg.solve(M, B)

                    # tổ hợp lồi
                    if np.all(lambdas >= -EPS):

                        z_val = (
                            lambdas[0] * y1
                            + lambdas[1] * y2
                        )

                        intersections.append({
                            "pair": (i, j),
                            "lambdas": lambdas,
                            "z": z_val
                        })

                except np.linalg.LinAlgError:
                    continue

    # =========================================================
    # 8. VÔ NGHIỆM
    # =========================================================

    if len(intersections) == 0:

        print("\n" + "=" * 50)
        print("KẾT LUẬN")
        print("=" * 50)
        print("Bài toán vô nghiệm.")
        print("=" * 50)

        return

    # =========================================================
    # 9. TÌM Z TỐI ƯU
    # =========================================================

    z_values = [item["z"] for item in intersections]

    if is_max:
        best_z = max(z_values)
    else:
        best_z = min(z_values)

    optimal_items = []

    for item in intersections:

        if abs(item["z"] - best_z) < 1e-7:

            optimal_items.append(item)

    # =========================================================
    # 10. VÔ SỐ NGHIỆM
    # =========================================================

    infinite_optimal = False

    if len(optimal_items) >= 2:
        infinite_optimal = True

    best_item = optimal_items[0]

    idx1, idx2 = best_item["pair"]

    best_lambdas = best_item["lambdas"]

    # =========================================================
    # 11. TÍNH NGHIỆM ĐẦY ĐỦ
    # =========================================================

    final_std = np.zeros(total_vars)

    final_std[idx1] = (
        best_lambdas[0]
        * multipliers[idx1]
    )

    final_std[idx2] = (
        best_lambdas[1]
        * multipliers[idx2]
    )

    # khử nhiễu
    final_std[np.abs(final_std) < EPS] = 0.0

    # =========================================================
    # 12. KHÔI PHỤC NGHIỆM GỐC
    # =========================================================

    orig_solution = np.zeros(len(x_conds))

    for i, m in enumerate(mapping):

        # x >= 0
        if m[0] == "normal":

            orig_solution[i] = final_std[m[1]]

        # x <= 0
        elif m[0] == "negative":

            orig_solution[i] = -final_std[m[1]]

        # tự do
        elif m[0] == "free":

            orig_solution[i] = (
                final_std[m[1]]
                - final_std[m[2]]
            )

    orig_solution[np.abs(orig_solution) < EPS] = 0.0

    # =========================================================
    # 13. KHÔNG GIỚI NỘI
    # =========================================================

    unbounded = False

    ys = []

    for p in points:

        if np.isfinite(p[1]):
            ys.append(p[1])

    if len(ys) > 0:

        if not is_max:

            if best_z <= min(ys) + 1e-7:
                unbounded = True

        else:

            if best_z >= max(ys) - 1e-7:
                unbounded = True

    if unbounded:

        print("\n" + "=" * 50)
        print("KẾT LUẬN")
        print("=" * 50)
        print("Bài toán không giới nội.")
        print("=" * 50)

        return

    # =========================================================
    # 14. GIÁ TRỊ Z THẬT
    # =========================================================

    actual_z = best_z

    if is_max:
        actual_z = -best_z

    # =========================================================
    # 15. KẾT LUẬN
    # =========================================================

    print("\n" + "=" * 50)
    print("KẾT LUẬN")
    print("=" * 50)

    if infinite_optimal:
        print("Bài toán có vô số nghiệm tối ưu.")
    else:
        print("Bài toán có nghiệm tối ưu duy nhất.")

    print("\n--- NGHIỆM GỐC ---")

    for i, val in enumerate(orig_solution):

        print(f"x{i+1} = {val:.4f}")

    print("\n--- NGHIỆM DẠNG CHUẨN ---")

    for j in range(total_vars):

        print(f"{var_labels[j]} = {final_std[j]:.4f}")

    print(f"\n{opt_type.upper()} Z = {actual_z:.4f}")

    print("=" * 50)

    # =========================================================
    # 16. VẼ ĐỒ THỊ
    # =========================================================

    print("\nĐang dựng đồ thị...")

    valid_points = []

    for k in valid_idx:

        xp, yp = points[k]

        if np.isfinite(xp) and np.isfinite(yp):

            valid_points.append((xp, yp, k))

    if len(valid_points) == 0:

        print("[!] Không đủ dữ liệu để vẽ.")
        if return_fig:
            return None
        return

    pts_arr = np.array([
        (p[0], p[1])
        for p in valid_points
    ])

    fig, ax = plt.subplots(figsize=(10, 8))

    ax.axhline(0, color='black', linewidth=1)
    ax.axvline(0, color='black', linewidth=1)

    # =========================================================
    # BAO LỒI
    # =========================================================

    if len(valid_points) >= 3:

        try:

            unique_pts = np.unique(pts_arr, axis=0)

            if len(unique_pts) >= 3:

                hull = ConvexHull(unique_pts)

                hull_pts = unique_pts[hull.vertices]

                ax.fill(
                    hull_pts[:, 0],
                    hull_pts[:, 1],
                    alpha=0.2,
                    color='orange',
                    hatch='\\\\',
                    label='Bao lồi'
                )

                for simplex in hull.simplices:

                    ax.plot(
                        unique_pts[simplex, 0],
                        unique_pts[simplex, 1],
                        color='orange'
                    )

        except Exception as e:

            print(f"[!] Không dựng được ConvexHull: {e}")

    # =========================================================
    # VẼ ĐIỂM
    # =========================================================

    ax.scatter(
        pts_arr[:, 0],
        pts_arr[:, 1],
        color='blue',
        s=70,
        zorder=5
    )

    for xp, yp, k in valid_points:

        ax.text(
            xp + 0.05,
            yp + 0.05,
            f"$a_{{{k+1}}}$",
            fontsize=10
        )

    # =========================================================
    # ĐƯỜNG QUÉT
    # =========================================================

    ax.axvline(
        x=target_x,
        color='red',
        linestyle='--',
        linewidth=2,
        label=f'x = {target_x:.2f}'
    )

    # =========================================================
    # ĐIỂM TỐI ƯU
    # =========================================================

    ax.scatter(
        [target_x],
        [best_z],
        color='red',
        marker='*',
        s=250,
        zorder=10,
        label='Điểm tối ưu'
    )

    # =========================================================
    # CẠNH TỐI ƯU
    # =========================================================

    ax.plot(
        [points[idx1][0], points[idx2][0]],
        [points[idx1][1], points[idx2][1]],
        color='purple',
        linewidth=3,
        label='Cạnh tối ưu'
    )

    # =========================================================
    # SCALE
    # =========================================================

    all_x = pts_arr[:, 0]
    all_y = pts_arr[:, 1]

    xmin = min(np.min(all_x), target_x) - 1
    xmax = max(np.max(all_x), target_x) + 1

    ymin = min(np.min(all_y), best_z) - 1
    ymax = max(np.max(all_y), best_z) + 1

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    ax.grid(True, linestyle=':', alpha=0.6)

    ax.set_xlabel("Trục x hình học")
    ax.set_ylabel("Trục z hình học")

    ax.set_title(
        f"ĐỒ THỊ BAO LỒI VECTƠ ({opt_type.upper()})"
    )

    ax.legend()

    fig.tight_layout()

    if show_plot:
        plt.show()
    elif not return_fig:
        plt.close(fig)

    if return_fig:
        return fig