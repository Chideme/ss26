window.onload = function(){
  document.getElementById('clickbutton').click()
}
document.addEventListener('DOMContentLoaded',() => {
  document.querySelector('#form').onsubmit = () => {
    const request = new XMLHttpRequest()
    const start_date = document.querySelector('#start_date').value;
    const end_date = document.querySelector('#end_date').value;
    const product = document.querySelector('#product').value;
    const frequency = document.querySelector('#frequency').value;
    const tank = document.querySelector('#tank').value;
    request.open('POST','/dashboard/reports');

    
    // when request finishes
    request.onload = () => {

      const report = JSON.parse(request.responseText);
      var sales_dates = report.SalesDate;
      var sales_data = report.SalesData;
      var profit_dates = report.ProfitDate;
      var profit_data = report.ProfitData;
      var tank_dates = report.TankDate;
      var tank_data = report.TankData;



          var ctx = document.getElementById("Sales");
          var sChart = new Chart(ctx, {
            type: 'line',
            data: {
              labels: sales_dates,
              datasets: [{
                data: sales_data,
                lineTension: 0,
                backgroundColor: '#333',
                borderColor: 'rgba(255,0,0,255)',
                borderWidth: 4,
                pointBackgroundColor: '#007bff'
              }]
            },
            options: {
              scales: {
                yAxes: [{
                  ticks: {
                    beginAtZero: true
                  }
                }]
              },
              legend: {
                display: false,
              },
              title: {
                display:true,
                text:frequency.concat(' ','Sales',' Report ','(Litres)')
              }
            }
          });
          var p_ctx = document.getElementById("GrossProfit");
          var pChart = new Chart(p_ctx, {
            type: 'bar',
            data: {
              labels: profit_dates,
              datasets: [{
                data: profit_data,
                lineTension: 0,
                backgroundColor: '#333',
                borderColor: 'rgba(255,0,0,255)',
                borderWidth: 4,
                pointBackgroundColor: '#007bff'
              }]
            },
            options: {
              scales: {
                yAxes: [{
                  ticks: {
                    beginAtZero: true
                  }
                }]
              },
              legend: {
                display: false,
              },
              title: {
                display:true,
                text:frequency.concat(' ','Gross Profit',' Report ','$')
              }
            }
          });
          var t_ctx = document.getElementById("TankVariance");
          var tankChart = new Chart(t_ctx, {
            type: 'line',
            data: {
              labels: tank_dates,
              datasets: [{
                data: tank_data,
                lineTension: 0,
                backgroundColor: '#333',
                borderColor: 'rgba(255,0,0,255)',
                borderWidth: 4,
                pointBackgroundColor: '#007bff'
              }]
            },
            options: {
              scales: {
                yAxes: [{
                  ticks: {
                    beginAtZero: true
                  }
                }]
              },
              legend: {
                display: false,
              },
              title: {
                display:true,
                text:frequency.concat(' ','Sales',' Report ','(Litres)')
              }
            }
          });

    }

    const data = new FormData();
    data.append('start_date',start_date);
    data.append('end_date',end_date);
    data.append('frequency',frequency);
    data.append('product',product);
    data.append('tank',tank);
    //send request
    request.send(data);

    return false;  

    }
    
    });

