#import "PQInventoryStore.h"

static NSString *const kKey = @"puzzlequest.inventory";

@implementation PQInventoryStore

+ (instancetype)sharedStore
{
    static PQInventoryStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQInventoryStore alloc] init];
    });
    return shared;
}

- (NSInteger)itemCount
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setItemCount:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
