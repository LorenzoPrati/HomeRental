function removeRoom(ordinale, proprietaid) {
    fetch('/removeRoom', {
        method: 'POST',
        body: JSON.stringify(
            {ordinale: ordinale, proprietaid: proprietaid}
        )
    }).then((_res) => {
        window.location.reload()
    });
}

function addRoom(proprietaid) {
    num_ospiti = document.getElementById('num_ospiti').value
    prezzo = document.getElementById('prezzo').value
    fetch('/addRoom', {
        method: 'POST',
        body: JSON.stringify(
            {proprietaid: proprietaid, num_ospiti: num_ospiti, prezzo: prezzo}
        )
    }).then((_res) => {
        window.location.reload()
    });
}



function removeAmenity(nome, proprietaid) {
    fetch('/removeAmenity', {
        method: 'POST',
        body: JSON.stringify(
            {nome: nome, proprietaid: proprietaid}
        )
    }).then((_res) => {
        window.location.reload()
    });
}

function addAmenity(proprietaid) {
    nome = document.getElementById('elimina_amenita').value
    fetch('/addAmenity', {
        method: 'POST',
        body: JSON.stringify(
            {nome: nome, proprietaid: proprietaid}
        )
    }).then((_res) => {
        window.location.reload()
    });
}

function rimuovi_proprieta(proprietaid) {
    fetch('/rimuovi_proprieta', {
        method: 'POST',
        body: JSON.stringify(
            {proprietaid: proprietaid}
        )
    }).then((_res) => {
        window.location.reload()
    });
}



