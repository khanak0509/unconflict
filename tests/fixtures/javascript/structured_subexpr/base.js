function total(items) {
  return items.reduce((s, x) => s + x.price, 0);
}

module.exports = { total };
