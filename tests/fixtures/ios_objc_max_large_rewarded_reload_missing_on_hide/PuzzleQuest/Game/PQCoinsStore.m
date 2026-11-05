#import "PQCoinsStore.h"

static NSString *const kKey = @"puzzlequest.coins";

@implementation PQCoinsStore

+ (instancetype)sharedStore
{
    static PQCoinsStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQCoinsStore alloc] init];
    });
    return shared;
}

- (NSInteger)balance
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setBalance:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
