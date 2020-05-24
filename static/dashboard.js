
document.addEventListener('DOMContentLoaded',() => {
  document.querySelector('#form').onsubmit = () => {
    const request = new XMLHttpRequest()
    const start_date = document.querySelector('#start_date').value;
    const end_date = document.querySelector('#end_date').value;
    const product = document.querySelector('#product').value;
    const frequency = document.querySelector('#frequency').value;
    const heading = document.querySelector('#heading').innerHTML;
   
    request.open('POST','/dashboard/reports');
    
    // when request finishes
    request.onload = () => {

      const report = request.responseText;
      
      
      document.querySelector('#json').innerHTML = report;
      
      
     

    }

    const data = new FormData();
    data.append('start_date',start_date);
    data.append('end_date',end_date);
    data.append('frequency',frequency);
    data.append('product',product);
    data.append('heading',heading);
    //send request
    request.send(data);

    return false;  

    }
    var ctx = document.getElementById("myChart");
        var myChart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            datasets: [{
              data: [15339, 21345, 18483, 24003, 23489, 24092, 12034],
              lineTension: 0,
              backgroundColor: 'transparent',
              borderColor: '#007bff',
              borderWidth: 4,
              pointBackgroundColor: '#007bff'
            }]
          },
          options: {
            scales: {
              yAxes: [{
                ticks: {
                  beginAtZero: false
                }
              }]
            },
            legend: {
              display: false,
            }
          }
        });
    
});