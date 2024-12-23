//fecth registered vechiles from the backend
export const getVechiles = async () => {
    const response = await fetch("http://localhost:8000/vechiles");
    const data = await response.json();
    return data;
}

//register a new vechile
export const addVechile = async (vechile) => {
    const response = await fetch("http://localhost:8000/vechiles/register", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(vechile)
    });
    const data = await response.json();
    return data;
}

