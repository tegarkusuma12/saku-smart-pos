const inventory = [

    {
        code: "PRD-001",
        name: "Indomie Goreng",
        category: "Makanan",
        stock: 42,
        price: 3500,
        status: "Aman"
    },

    {
        code: "PRD-002",
        name: "Aqua 600ml",
        category: "Minuman",
        stock: 8,
        price: 3500,
        status: "Menipis"
    },

    {
        code: "PRD-003",
        name: "Teh Botol",
        category: "Minuman",
        stock: 25,
        price: 4000,
        status: "Aman"
    },

    {
        code: "PRD-004",
        name: "Kopi Sachet",
        category: "Minuman",
        stock: 5,
        price: 2500,
        status: "Menipis"
    },

    {
        code: "PRD-005",
        name: "Roti Cokelat",
        category: "Makanan",
        stock: 0,
        price: 7000,
        status: "Habis"
    },

    {
        code: "PRD-006",
        name: "Sabun Mandi",
        category: "Kebutuhan",
        stock: 18,
        price: 6500,
        status: "Aman"
    },

    {
        code: "PRD-007",
        name: "Minyak 1 Liter",
        category: "Kebutuhan",
        stock: 7,
        price: 18000,
        status: "Menipis"
    }

];


document.addEventListener("DOMContentLoaded", function () {

    renderInventory();


    const search = document.getElementById("inventorySearch");

    const filter = document.getElementById("stockFilter");


    if (search) {

        search.addEventListener(
            "input",
            renderInventory
        );

    }


    if (filter) {

        filter.addEventListener(
            "change",
            renderInventory
        );

    }

});


function renderInventory() {

    const table = document.getElementById("inventoryTable");

    if (!table) {
        return;
    }


    const searchValue =
        document
            .getElementById("inventorySearch")
            ?.value
            .toLowerCase() || "";


    const filterValue =
        document
            .getElementById("stockFilter")
            ?.value || "all";


    const filtered = inventory.filter(function (item) {

        const matchesSearch =
            item.name
                .toLowerCase()
                .includes(searchValue) ||

            item.code
                .toLowerCase()
                .includes(searchValue);


        const matchesFilter =
            filterValue === "all" ||
            item.status === filterValue;


        return matchesSearch && matchesFilter;

    });


    table.innerHTML = filtered.map(function (item) {

        let badgeClass = "stock-safe";

        if (item.status === "Menipis") {
            badgeClass = "stock-low";
        }

        if (item.status === "Habis") {
            badgeClass = "stock-empty";
        }


        return `

            <tr>

                <td>
                    ${item.code}
                </td>

                <td>
                    <strong>
                        ${item.name}
                    </strong>
                </td>

                <td>
                    ${item.category}
                </td>

                <td>
                    ${item.stock}
                </td>

                <td>
                    ${formatRupiah(item.price)}
                </td>

                <td>

                    <span class="stock-badge ${badgeClass}">
                        ${item.status}
                    </span>

                </td>

                <td class="text-end">

                    <button
                        class="btn btn-sm btn-outline-primary"
                        onclick="addStock('${item.code}')"
                    >

                        <i class="fa-solid fa-plus"></i>

                    </button>

                </td>

            </tr>

        `;

    }).join("");

}


function addStock(code) {

    const item = inventory.find(
        product => product.code === code
    );


    if (!item) {
        return;
    }


    item.stock += 10;


    if (item.stock === 0) {

        item.status = "Habis";

    } else if (item.stock <= 10) {

        item.status = "Menipis";

    } else {

        item.status = "Aman";

    }


    renderInventory();

}


function formatRupiah(value) {

    return new Intl.NumberFormat(
        "id-ID",
        {
            style: "currency",
            currency: "IDR",
            maximumFractionDigits: 0
        }
    ).format(value);

}