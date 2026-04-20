let name = "Geeks for Geeks";
let reverseString = '';
for (let i = 15; i >= 0; i--) {
    reverseString += name[i];
}
console.log(reverseString);
console.log(name[14]); // check last character
console.log(name[0]); // check first character
console.log(name.length); // check string length