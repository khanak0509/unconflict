function total(items) {
  return items.reduce((s, x) => s + x.price * x.qty, 0);
}

module.exports = { total };
