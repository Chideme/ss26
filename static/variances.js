document.addEventListener('DOMContentLoaded',() => {
  document.querySelector('#form').onsubmit = () => {
    const request = new XMLHttpRequest()
    const start_date = document.querySelector('#start_date').value;
    const end_date = document.querySelector('#end_date').value;
    const tank = document.querySelector('#tank').value;
    
   console.log(start_date)
    request.open('POST','/dashboard/variance');
    
    // when request finishes
    request.onload = () => {

      const report = request.responseText;
      
      
      document.querySelector('#json').innerHTML = report;
      


    }

    const data = new FormData();
    data.append('start_date',start_date);
    data.append('end_date',end_date);
    data.append('tank',tank);
    
    //send request
    request.send(data);

    return false;  

    }
    
});