const toggleButton = document.getElementById('outday-switch');
const userInfoTrs = document.getElementsByClassName('user-info-row');

const date_today = document.getElementById('shadow-today');
const outday = document.getElementsByClassName('shadow-item');

const toggleSwitch = (outdayFlag) => {
  if (outdayFlag) {
    console.log(outdayFlag);
    for (let i = 0; i < userInfoTrs.length; i++) {
      console.log(outday[i].textContent);
      if (outday[i].textContent > date_today.textContent || outday[i].textContent == 'None') {
        console.log(`${i}: visible`);
        userInfoTrs[i].style.display = "table-row";
      } else {
        console.log(`${i}: unvisible`);
        userInfoTrs[i].style.display = "none";
      }
    }
  } else {
    console.log(outdayFlag);
    for (let i = 0; i < userInfoTrs.length; i++) {
      console.log(outday[i].textContent);
      if (outday[i].textContent > date_today.textContent || outday[i].textContent == 'None') {
        console.log(`${i}: unvisible`);
        userInfoTrs[i].style.display = "none";
      } else {
        console.log(`${i}: visible`);
        userInfoTrs[i].style.display = "table-row";
      }
    }
  }
}

let displayFlag = false;
toggleButton.addEventListener('click', () => {
  console.log('On click!');
  if (displayFlag == false) {
    toggleSwitch(displayFlag);
    displayFlag = true;
  } else {
    toggleSwitch(displayFlag);
    displayFlag = false;
  }
});
