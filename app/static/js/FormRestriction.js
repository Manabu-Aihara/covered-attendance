// お前はもう、宣言されている
// const selectArea = document.getElementsByClassName('form-control')[0];
const selectChildren = selectArea.options;

// 開始時刻・終了時刻
const timeForms = document.getElementsByClassName('restrict-form');
// 入力制限処理トグル関数
const toggleRestrictState = (flag) => {
  if (flag == true) {
    for (let i = 0; i < timeForms.length; i++) {
      timeForms[i].readOnly = true;
      timeForms[i].style.backgroundColor = "gainsboro";
    }
  } else {
    for (let i = 0; i < timeForms.length; i++) {
      timeForms[i].readOnly = false;
      timeForms[i].style.backgroundColor = "";
    }
  }
}

const startTimeForm = timeForms[0];
const endTimeForm = timeForms[1];

const workTime = document.getElementById('worktime');

// Param: diffNum 何時間後
const reflectTimeForm = (diffNum) => {
  // 半休用
  let halfTime, plus_m;
  if (Number.isInteger(diffNum) === false) {
    halfTime = Math.floor(diffNum) / 2;
    diffNum = halfTime;
    console.log(`---${diffNum}---`);
    separate_m = halfTime - Math.floor(halfTime);
    plus_m = separate_m * 60;
  }
  /**
 * input type=date:値の変更の感知にはinput
 */
  startTimeForm.addEventListener('input', () => {
    let [h, m] = startTimeForm.value.split(':');
    // 半休用
    let over_if = Number(m) + plus_m;
    console.log(over_if);
    if (over_if >= 60) {
      plus_m = over_if - 60;
      diffNum += 1;
    } else {
      if (h < 10) {
        const oneDigit = Number(h) + diffNum
        console.log(`***${diffNum}***`);
        /**
         * 数字を指定した桁数まで0埋めする
            https://gray-code.com/javascript/fill-numbers-with-zeros/
        */
        endTimeForm.value = `${oneDigit.toString().padStart(2, '0')}:${Number(m) + plus_m}`;
      } else {
        endTimeForm.value = `${Number(h) + diffNum}:${Number(m) + plus_m}`;
      }
    }
  });
}

const restrictCollection = () => {
  // console.log("Called!")
  console.log(selectChildren.selectedIndex);

  // for(let option in selectChildren){
  console.log(selectChildren);
  // for (let i = 0; i < selectChildren.length; i++) {
  if ((selectChildren.selectedIndex) === 4 || (selectChildren.selectedIndex) === 6 || (selectChildren.selectedIndex) === 8 || (selectChildren.selectedIndex) === 9 || (selectChildren.selectedIndex) === 17 || (selectChildren.selectedIndex) === 18 || (selectChildren.selectedIndex) === 19 || (selectChildren.selectedIndex) === 20) {
    toggleRestrictState(true);
  } else if ((selectChildren.selectedIndex) === 10 || (selectChildren.selectedIndex) === 13) {
    toggleRestrictState(false);
    reflectTimeForm(1);
  } else if ((selectChildren.selectedIndex) === 11 || (selectChildren.selectedIndex) === 14) {
    toggleRestrictState(false);
    reflectTimeForm(2);
  } else if ((selectChildren.selectedIndex) === 12 || (selectChildren.selectedIndex) === 15) {
    toggleRestrictState(false);
    reflectTimeForm(3);
  } else if ((selectChildren.selectedIndex) === 5 || (selectChildren.selectedIndex) === 7) {
    toggleRestrictState(false);
    console.log(workTime)
    reflectTimeForm(workTime.value)
  } else {
    toggleRestrictState(false);
  }
  // }
}

selectArea.addEventListener('change', restrictCollection);
