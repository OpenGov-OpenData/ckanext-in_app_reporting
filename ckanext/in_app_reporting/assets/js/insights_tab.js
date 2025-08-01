$(document).ready(function () {
    const resourceIdElement = document.querySelector('[data-resource-id]');
    if (!resourceIdElement) return;
    const resourceId = resourceIdElement.getAttribute('data-resource-id');
    fetch('/api/3/action/metabase_sql_questions_list', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ resource_id: resourceId })
    })
    .then(response => response.json())
    .then(result => {
    const data = result.result;
    const tbody = document.getElementById('metabase-cards-body');
    const loadingRow = document.getElementById('sql-questions-loading');
    if (loadingRow) loadingRow.remove();

    if (data.length > 0) {
        data.forEach(card => {
            tbody.insertAdjacentHTML('beforeend', `
                <tr>
                <td><a href="/insights?return_to=/${card.type}/${card.id}">${card.name}</a></td>
                <td>${card.type} (SQL)</td>
                <td>${card.updated_at}</td>
                </tr>
            `);
        });
    }
    })
});
